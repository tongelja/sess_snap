#!/bin/python

#/tools/python/virtual/dba/bin/python

##########################
##
##
##
##
##################################


###########################
##
## Import
###
#####################################

import os, re, sys, getopt, operator, time, cx_Oracle, binascii, getpass
sys.path.append(os.path.abspath('bin'))


##############################
##
## Functions
##
#######################################

##
## usage
##
def usage_exit(message):
    print message
    print "Usage:"
    print os.path.abspath( __file__ ),  '\n \
    Options: \n\n \
          -s ORACLE_SESSION_ID  \n \
             Session ID (SID) in Oracle \n\n \
        [ -c CONNECTION_STRING ] \n \
             Connection String Format:  SID:Hostname[User:Password:Port] \n\n \
        [ -f SNAPSHOT[:LINES],... ] \n \
             Snapshot Options: TRANSACTION \n \
                               METRIC \n \
                               STAT \n \
                               EVENT \n \
                               WAIT \n \
                               IO \n \
                               SQL_TEXT \n \
                               PROCESS \n \
                               LONGOP \n \
                               SEGSTAT \n \
                               LOCK \n \
                               SQLMONITOR \n \n '

    sys.exit(2)



##
## main
##
def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "c:s:f:")
    except getopt.GetoptError, err:
        print str(err)
        usage_exit('getopt error:')

    connect    = None
    SID        = None
    format     = None

    for o, a in opts:
        if o in ('-c'):
            connect = a
        elif o in ('-f'):
            format = a
        elif o in ('-s'):
            SID = a
        else:
            assert False, "unhandled option"

    if SID is None:
        usage_exit('No Session ID specified')

    if format is None:
        format = 'TRANSACTION,IO,WAIT,SQL_TEXT,LONGOP,STAT,EVENT,SQLMONITOR'

    

    my_snap = Session_Snap(conn, format)
    my_snap.getDbInfo()

    while 1 == 1:
        try:
            my_snap.create_snapshot(SID)
        except KeyboardInterrupt:
            print 'Exiting...'
            sys.exit(0)

        
def max_length(a, b):
    c = len(str(a))
    d = len(str(b))
    if c > d:       return a
    else:           return b
    

    
class Session_Snap:
    def __init__(self, conn, display_items):
    
        self.delimiter                  = '-----------------------------'
        self.column_format_01           = '%-45s %-2s'
        self.column_format_02           = '%-60s %15s %20s'
        self.column_format_03           = '%-60s %15.1f %15.1f %-4s'
        self.column_format_04           = '%-80s'
        self.column_format_05           = '%-20s'

        self.sleep_time                 = 5
        self.db                         = conn
        self.sess                       = {}
        self.display_items              = []
        self.print_lines                = {}

   
        for i in display_items.upper().split(','):
            j = i.split(':')
            self.display_items.append( j[0] )

            if len(j) > 1:       
                self.print_lines[j[0]] = int( j[1] )
            else:                
                self.print_lines[j[0]] = 5


 
    def create_snapshot(self, SID):

        self.snapshot_switch = { 'TRANSACTION':   self.transaction_snapshot,
                                 'PROCESS':       self.proc_snapshot,
                                 'IO':            self.io_snapshot,
                                 'WAIT':          self.wait_snapshot,
                                 'SQL_TEXT':      self.sql_text_snapshot,
                                 'STAT':          self.stats_snapshot,
                                 'EVENT':         self.events_snapshot,
                                 'METRIC':        self.sess_metrics_snapshot,
                                 'LONGOP':        self.sess_longop_snapshot,
                                 'SEGSTAT':       self.segstat_snapshot,
                                 'SQLMONITOR':    self.sqlmonitor_snapshot,
                                 'LOCK':          self.lock_snapshot,
                               }

        self.print_switch = {    'TRANSACTION':   self.print_transaction,
                                 'PROCESS':       self.print_process,
                                 'IO':            self.print_io,
                                 'WAIT':          self.print_wait,
                                 'SQL_TEXT':      self.print_sql_text,
                                 'STAT':          self.print_stats,
                                 'EVENT':         self.print_events,
                                 'METRIC':        self.print_sess_metrics,
                                 'LONGOP':        self.print_sess_longop,
                                 'SEGSTAT':       self.print_segstat,
                                 'SQLMONITOR':    self.print_sqlmonitor,
                                 'LOCK':          self.print_lock,
                            }

        self.check_sid(SID)
        self.get_sess_info(SID)
        for i in self.display_items:
            self.snapshot_switch[i](1, SID)
 
        time.sleep(self.sleep_time)
    
        self.check_sid(SID)
        for i in self.display_items:
            self.snapshot_switch[i](2, SID)
 
        os.system('clear')
   
        self.print_sess_info()
        for i in self.display_items:
            self.print_switch[i]()
    
    
    def check_sid(self, SID):
        cursor = self.db.cursor()
        sql_stmt = "select count(*) from v$session where sid = " + SID
        #print_sql_stmt
    
        cursor.execute(sql_stmt)
        rows = cursor.fetchall()
    
        if rows[0][0] == 0:
            print 'SID ' + str(SID) + ' does not exist.'
            sys.exit(2)
          
       
    
    def print_events(self):
        s             = self.sess
        num_rows      = self.print_lines['EVENT'] 
        header_format = self.column_format_02
        line_format   = self.column_format_03

        if len( s['event']['delta']) < num_rows:
            start = 0 
        else:   
            start = len( s['event']['delta']) - num_rows 
    
        for i in range(start, len( s['event']['delta']) ):
            if i == start:
                print '\n-- Events ' + self.delimiter
                print header_format % ('Event', 'Delta', 'Rate')
    
            print line_format % (s['event']['delta'][i][0], s['event']['delta'][i][1], s['event']['delta'][i][1]/self.sleep_time, '/Sec' )
    
   
    def print_segstat(self):
        s             = self.sess
        num_rows      = self.print_lines['SEGSTAT']
        header_format = self.column_format_02
        line_format   = self.column_format_03

        if len( s['segstat']['delta']) < num_rows:
            start = 0
        else:
            start = len( s['segstat']['delta']) - num_rows

        for i in range(start, len( s['segstat']['delta']) ):
            if i == start:
                print '\n-- Segment Stats ' + self.delimiter
                print header_format % ('Object - Statistic', 'Delta', 'Rate')

            print line_format % (s['segstat']['delta'][i][0], s['segstat']['delta'][i][1], s['segstat']['delta'][i][1]/self.sleep_time, '/Sec' )


 
    
    def print_sqlmonitor(self):
        if self.sess['db_info']['version'].split('.')[0] == '10':
            return

        s             = self.sess
        line_format   = '%-4s %-' + str(s['sql_monitor']['max_op_length'] +5) + 's %-' + str(s['sql_monitor']['max_obj_length'] ) + 's %10s %6s %6s %10s %6s %6s %6s %6s  %6s %6s %6s  %4s %4s %5s'
        num_rows      = self.print_lines['SQLMONITOR']
        start         = 0

        total_delta = 0
        for i in range(start, len( s['sql_monitor']['plan']) ):

            if s['sql_monitor']['plan'][i]['sql_id'] != s['old_sql_monitor']['plan'][i]['sql_id']:
                total_delta = 0
            else:
                current_activity =  s['sql_monitor']['plan'][i]['output_rows'] +  \
                                    s['sql_monitor']['plan'][i]['physical_read_requests'] +  \
                                    s['sql_monitor']['plan'][i]['physical_write_requests'] +  \
                                    s['sql_monitor']['plan'][i]['physical_write_bytes'] +  \
                                    s['sql_monitor']['plan'][i]['workarea_mem'] +  \
                                    s['sql_monitor']['plan'][i]['starts'] +  \
                                    s['sql_monitor']['plan'][i]['workarea_tempseg']
                previous_activity = s['old_sql_monitor']['plan'][i]['output_rows'] + \
                                    s['old_sql_monitor']['plan'][i]['physical_read_requests'] + \
                                    s['old_sql_monitor']['plan'][i]['physical_write_requests'] + \
                                    s['old_sql_monitor']['plan'][i]['physical_write_bytes'] + \
                                    s['old_sql_monitor']['plan'][i]['starts'] + \
                                    s['old_sql_monitor']['plan'][i]['workarea_mem'] + \
                                    s['old_sql_monitor']['plan'][i]['workarea_tempseg']

        
                total_delta += current_activity - previous_activity 

        for i in range(start, len( s['sql_monitor']['plan']) ):
            if i == start:
                print '\n-- SQL Monitor ' + self.delimiter
                print 'SQL ID           : ' + s['sql_monitor']['sql_id']
                print 'Child Number     : ' + str(s['sql_monitor']['child_number'])
                print 'Plan Hash Value  : ' + str(s['sql_monitor']['plan_hash_value'])

                print line_format % (' ',  '         ', '      ', 'Est',  'Act',  ' ',   'Est IO', 'PhyRd', 'PhyWrt', 'PhyWrt', 'PhyRd', 'Est',  '',    '',     ' ',   ' ',    '')
                print line_format % ('ID', 'Operation', 'Object', 'Rows', 'Rows', 'Exe', 'Cost',   'Req',   'Req',    'Bytes',  'Bytes', 'Temp', 'Mem', 'Temp', 'CPU%', 'IO%', '')
                print line_format % ('--', '---------', '------', '----', '----', '---', '----',   '-----', '------', '------', '-----', '----', '---', '----', '----', '---', '')

            if s['sql_monitor']['plan'][i]['sql_id'] != s['old_sql_monitor']['plan'][i]['sql_id']:
                delta = ''
            else:
                current_activity =  s['sql_monitor']['plan'][i]['output_rows'] +  \
                                    s['sql_monitor']['plan'][i]['physical_read_requests'] +  \
                                    s['sql_monitor']['plan'][i]['physical_write_requests'] +  \
                                    s['sql_monitor']['plan'][i]['physical_write_bytes'] +  \
                                    s['sql_monitor']['plan'][i]['workarea_mem'] +  \
                                    s['sql_monitor']['plan'][i]['starts'] +  \
                                    s['sql_monitor']['plan'][i]['workarea_tempseg']  
                previous_activity = s['old_sql_monitor']['plan'][i]['output_rows'] + \
                                    s['old_sql_monitor']['plan'][i]['physical_read_requests'] + \
                                    s['old_sql_monitor']['plan'][i]['physical_write_requests'] + \
                                    s['old_sql_monitor']['plan'][i]['physical_write_bytes'] + \
                                    s['old_sql_monitor']['plan'][i]['starts'] + \
                                    s['old_sql_monitor']['plan'][i]['workarea_mem'] + \
                                    s['old_sql_monitor']['plan'][i]['workarea_tempseg']  
                if current_activity != previous_activity:
                    #delta = '<<-- ' + "{0:.1f}".format(((current_activity-previous_activity)*100)/total_delta) + '%'
                    delta = '<<-- ' + str(((current_activity-previous_activity)*100)/total_delta)   + '%'
                else:
                    delta = ''

            num_lines=len( s['sql_monitor']['plan']) 
            #if num_lines < 30 and 1==2 :
            if 1==1 :
                try:
                    cpu_pct             = format_number( (s['sql_monitor']['plan'][i]['cpu_tm']*100)/s['sql_monitor']['delta_tm_01'] ) 
                except (ZeroDivisionError, TypeError):
                    cpu_pct            = ' '
                try:
                    db_pct              = format_number( (s['sql_monitor']['plan'][i]['db_tm']*100)/s['sql_monitor']['delta_tm_01'] )   
                except (ZeroDivisionError, TypeError):
                    db_pct             = ' '
                try:
                    total_io_bytes_pct  = format_number( ((int(s['sql_monitor']['plan'][i]['rd_io_bytes'])+int(s['sql_monitor']['plan'][i]['wr_io_bytes']))*100) / (int(s['sql_monitor']['total_io_bytes']))) 
                except (ZeroDivisionError, TypeError):
                    total_io_bytes_pct = ' '
                    
                print line_format % (s['sql_monitor']['plan'][i]['plan_id'],
                                     s['sql_monitor']['plan'][i]['plan_operation'],
                                     s['sql_monitor']['plan'][i]['plan_object'],
                                     format_number(s['sql_monitor']['plan'][i]['plan_cardinality']),
                                     format_number(s['sql_monitor']['plan'][i]['output_rows']),
                                     format_number(s['sql_monitor']['plan'][i]['starts']),
                                     format_number(s['sql_monitor']['plan'][i]['plan_io_cost']),
                                     format_number(s['sql_monitor']['plan'][i]['physical_read_requests']),
                                     format_number(s['sql_monitor']['plan'][i]['physical_write_requests']),
                                     format_number(s['sql_monitor']['plan'][i]['physical_write_bytes'], 1024),            ## 10
                                     format_number(s['sql_monitor']['plan'][i]['physical_read_bytes'], 1024),   
                                     format_number(s['sql_monitor']['plan'][i]['plan_temp_space'], 1024), 
                                     format_number(s['sql_monitor']['plan'][i]['workarea_mem'], 1024), 
                                     format_number(s['sql_monitor']['plan'][i]['workarea_tempseg'], 1024), 
                                     cpu_pct,
                                     total_io_bytes_pct,
                                     delta)
            else:
                if delta != '':
                    print line_format % (s['sql_monitor']['plan'][i]['plan_id'],
                                         s['sql_monitor']['plan'][i]['plan_operation'],
                                         s['sql_monitor']['plan'][i]['plan_object'],
                                         format_number(s['sql_monitor']['plan'][i]['plan_cardinality']),
                                         format_number(s['sql_monitor']['plan'][i]['output_rows']),
                                         format_number(s['sql_monitor']['plan'][i]['plan_io_cost']),
                                         format_number(s['sql_monitor']['plan'][i]['physical_read_requests']),
                                         format_number(s['sql_monitor']['plan'][i]['physical_write_requests']),
                                         format_number(s['sql_monitor']['plan'][i]['physical_write_bytes'], 1024),
                                         format_number(s['sql_monitor']['plan'][i]['plan_temp_space'], 1024),
                                         format_number(s['sql_monitor']['plan'][i]['workarea_mem'], 1024),
                                         format_number(s['sql_monitor']['plan'][i]['workarea_tempseg'], 1024),
                                         delta)


 
    def print_stats(self):
        s             = self.sess
        num_rows      = self.print_lines['STAT']
        header_format = self.column_format_02
        line_format   = self.column_format_03


        if len( s['stat']['delta']) < num_rows:
            start = 0
        else:
            start = len( s['stat']['delta']) - num_rows 
    
        for i in range(start, len( s['stat']['delta']) ):
            if i == start:
                print '\n-- Statistics ' + self.delimiter
                print header_format % ('Statistic', 'Delta', 'Rate')
    
            print line_format % (s['stat']['delta'][i][0], s['stat']['delta'][i][1], s['stat']['delta'][i][1]/self.sleep_time, '/Sec' )
    
    
    
    def print_sess_metrics(self):
        s           = self.sess
        line_format = self.column_format_01
        columns     = 2

        field_names = {'cpu'               :  'CPU',
                       'physical_reads'    :  'Phys. Reads',
                       'logical_reads'     :  'Log. Reads',
                       'pga_memory'        :  'PGA Memory',
                       'hard_parses'       :  'Hard Parses',
                       'soft_parses'       :  'Soft Parses',
                       'physical_read_pct' :  'Phys. Read %',
                       'logical_read_pct'  :  'Log. Read %',
                      }

        i            = 0
        line         = ''
        stat_format  = '%-' + str( len( reduce(max_length, field_names.values()) )+2) + 's %-10s'
        print_fields = [ 'cpu', 'pga_memory',
                         'physical_reads', 'logical_reads',
                         'hard_parses', 'soft_parses',
                         'physical_read_pct', 'logical_read_pct' ]

        for j in print_fields:

            if i == 0:
                print '\n-- Sess Metrics ' + self.delimiter
     
            if j is not None:
                stat = stat_format % ( field_names[j] + ': ' , str(s['metric'][j]) )
            else:
                stat = ' '

            line = line + line_format % ( stat, ' ' )
    
            if (i+1)% columns  == 0:
                print line
                line = ''
    
            if i == len( s['metric'] )  :
                if (i+1)%columns > 0 :
                    print line
            i = i + 1 
    
    
    def print_sess_info(self):

        s           = self.sess
        line_format = self.column_format_01
        columns     = 4

        field_names = { 'sid':                     'SID', 
                        'sid_serial':              'SID, Serial#',
                        'serial#':                 'Serial#',
                        'username':                'Username',
                        'taddr':                   'Trans Addr',
                        'lockwait':                'Lock Addr',
                        'status':                  'Status',
                        'osuser':                  'Clnt OS User',
                        'process':                 'Clnt OS PID',
                        'machine':                 'Clnt Host',
                        'terminal':                'Terminal',
                        'module':                  'Clnt Module',
                        'program':                 'Program',
                        'saddr':                   'Sess Addr',
                        'paddr':                   'Proc Addr',
                        'taddr':                   'Tran Addr',
                        'sql_address':             'SQL Addr',
                        'sql_hash_value':          'SQL Hash',
                        'sql_id':                  'SQL ID',
                        'sql_child_number':        'SQL Child#',
                        'row_wait_obj#':           'R Wait Obj#',
                        'row_wait_row#':           'R Wait Row#',
                        'logon_time':              'Logon Time',
                        'last_call_et':            'Last Call ET',
                        'blocking_session':        'Blk Session',
                        'event':                   'Event',
                        'p1':                      'P1',
                        'p1text':                  'P1 Text',
                        'p2':                      'P2',
                        'p2text':                  'P2 Text',
                        'p3':                      'P3',
                        'p3text':                  'P3 Text',
                        'seconds_in_wait':         'Sec in Wait',
                        'state':                   'State',
                        'wait_time':               'Wait Time',
                        'instance_name':           'Instance',
                        'host_name':               'Host',
                        'sysdate':                 'Date',
                        'current_scn':             'Cur SCN',
                    }
    
        s['sess']['machine']      = re.sub('.hq.navteq.com', '', s['sess']['machine'])
        try:
            s['sess']['module']   = re.sub('\(.*', '', s['sess']['module'])
        except: 
            s['sess']['module']   = 'None'
        s['sess']['host_name']    = s['sess']['host_name'].replace('.hq.navteq.com', '')
        s['sess']['sid_serial']   = '(' + str( s['sess']['sid'] )  + ', ' + str( s['sess']['serial#'] ) + ')'
        s['sess']['saddr']        = binascii.hexlify(s['sess']['saddr']).upper()
        s['sess']['paddr']        = binascii.hexlify(s['sess']['paddr']).upper()
        s['sess']['sql_address']  = binascii.hexlify(s['sess']['sql_address']).upper()
                      

        i            = 0
        line         = ''
        stat_format  = '%-' + str( len( reduce(max_length, field_names.values()) )+2) + 's %-10s'
        print_fields = ['sysdate', 'host_name', 'instance_name', 'current_scn',
                        'sid_serial', 'username', 'logon_time', 'last_call_et', 
                        'osuser', 'machine', 'module', 'sql_id', 
                        'saddr', 'paddr', 'taddr', 'sql_address', 'sql_child_number',
                        'status', 'blocking_session' ]

        for j in print_fields:
            if i == 0:
                print '\n-- Session ' + self.delimiter

            if j is not None:
                stat = stat_format % ( field_names[j] + ': ' , str(s['sess'][j]) )
            else:
                stat = ' '

            line = line + line_format % ( stat, ' ' )


            if (i+1)% columns  == 0:
                print line
                line = ''

            if i == len( print_fields ) -1 :
                if (i+1)%columns > 0 :
                    print line

            i = i + 1



    def print_lock(self):
        s           = self.sess
        line_format = self.column_format_05
    
        i    = 0
        line = '' 
        print_fields = [ 'addr', 'id1', 'id2', 'lmode', 'type', 'request', 'object_type', 'object_name' ]
        print_header = [ 'Addr', 'Id1', 'Id2', 'Lock Mode', 'Type', 'Request Mode', 'Object Type', 'Object Name' ]
     
        start = 0
        end   = len(s['lock']) -1
       
        for i in range(start, end):
            if i == 0:
                print '\n-- Locks ' + self.delimiter
                for j in print_header:
                    line = line + line_format % ( j )
                print line
                line = ''

                
            for j in print_fields:
                line = line + line_format % ( s['lock'][i][j] )
            print line
            line = ''
    
    def print_wait(self):
        s           = self.sess
        line_format = self.column_format_04
    
        if s['wait']['wait_time'] == 0:
            wait_state =  s['wait']['state'] + ', ' + str( s['wait']['seconds_in_wait'] ) + ' sec. in wait'
        else:
            wait_state =  'On CPU (Previous wait event listed)'
    
        ptext = ''
        if s['wait']['p1text'] != None:
            ptext = s['wait']['p1text'] + '=' + str(s['wait']['p1'])
        if s['wait']['p2text'] != None:
            ptext = ptext + ', ' + s['wait']['p2text'] + '=' + str(s['wait']['p2'])
        if s['wait']['p3text'] != None:
            ptext = ptext + ', ' + s['wait']['p3text'] + '=' + str(s['wait']['p3'])
    
    
        print '\n-- Wait Event ' + self.delimiter
        print line_format % ( 'Event:  ' + s['wait']['event'] )
        print line_format % ( 'PText:  ' +  ptext )
        print line_format % ( 'State:  ' +  wait_state )
    
        if s['wait']['blocking_session'] != None:
            print line_format % ('Blocker:  ' +  'SID=' + str(s['wait']['blocking_session']) + ', Obj#=' + str(s['wait']['row_wait_obj#']) )
    
    
       
    
    def print_transaction(self):
        s           = self.sess
        line_format = self.column_format_01
        columns     = 4
    
        if len(s['trans']) == 0:
            return 0 
    
        field_names = { 'Xidusn':          'Undo Seg Num',
                        'Xidslot':         'Undo Slot Num',
                        'Xidsqn':          'Undo Seq Num',
                        'Ubafil':          'UBA File',
                        'Start_Ubafil':    'Strt UBA File',
                        'Ubablk':          'UBA Block',
                        'Start_Ubablk':    'Strt UBA Block',
                        'Ubasqn':          'UBA Seq#',
                        'Start_Ubasqn':    'Strt UBA Seq#',
                        'Ubarec':          'UBA Rec#',
                        'Start_Ubarec':    'Strt UBA Rec#',
                        'Status':          'Status',
                        'Start_Time':      'Strt Time',
                        'Start_SCN':      'Strt SCN',
                        'Used_Ublk':       'Undo Blks Used',
                        'Used_Urec':       'Undo Rcds Used',
                        'Log_IO':          'Logical I/O',
                        'Phy_IO':          'Physical I/O',
                        'Cr_Get':          'Cons Gets',
                        'Cr_Change':       'Cons Changes',
                      }
                       

        i            = 0
        line         = ''
        stat_format  = '%-' + str( len( reduce(max_length, field_names.values()) )+2) + 's %-10s'
        print_fields = ['Xidusn', 'Xidslot', 'Xidsqn', None,
                        'Ubafil', 'Ubablk', 'Ubasqn', 'Ubarec',
                        'Start_Ubafil', 'Start_Ubablk', 'Start_Ubasqn', 'Start_Ubarec',
                        'Log_IO', 'Phy_IO', 'Cr_Get', 'Cr_Change',
                        'Status', 'Start_Time', 'Start_SCN', None,
                        'Used_Ublk', 'Used_Urec', None, None ]

        for j in print_fields:
            if i == 0:
                print '\n-- Transaction ' + self.delimiter
   
            if j is not None:
                stat = stat_format % ( field_names[j] + ': ' , str(s['trans'][j]) )
            else:
                stat = ' '

            line = line + line_format % ( stat, ' ' )
 
    
            if (i+1)% columns  == 0:
                print line
                line = ''
    
            if i == len( print_fields ) -1 :
                if (i+1)%columns > 0 :
                    print line
    
            i = i + 1
    
    def print_sql_text(self):
        s      = self.sess
        lines  = self.print_lines['SQL_TEXT']

        if len(s['sql_text']) == 0:
            return 0
    
        start = 0
        if len(s['sql_text']) > lines:
            end = lines
        else:
            end = len(s['sql_text'])
    
        for i in range(start, end ) :
            if i == 0:
                print ''
                print '-- SQL Text (' + str(s['sess']['sql_id']) + ') ' + self.delimiter
                print s['sql_text'][int(i)].strip()

            else:
                try:
                    print '    ' + s['sql_text'][int(i)].strip()
                except:
                    print ' '
    
    
    def print_io(self):
        s           = self.sess
        line        = ''
        columns     = 3
        line_format = self.column_format_01
    
        if len(s['io']) == 0:
            return 0
    
        field_names = { 'block_gets': 'Block Gets',
                        'consistent_gets': 'Cons. Gets',
                        'physical_reads': 'Physical Reads',
                        'block_changes': 'Block Changes',
                        'consistent_changes': 'Cons. Changes'
                      }
    
        i            = 0
        stat_format  = '%-' + str( len( reduce(max_length, field_names.values()) )+2) + 's %-10s'
        print_fields = ['block_gets', 'consistent_gets', 'physical_reads', 'block_changes', 'consistent_changes']

        for j in print_fields:
            if i == 0:
                print ''
                print '-- Sess I/O ' + self.delimiter
    
            if j is not None:
                stat = stat_format % ( field_names[j] + ': ' , str(s['io'][j]) )
            else:
                stat = ' '

            line = line + line_format % ( stat, ' ' )
 
            if (i+1)% columns  == 0:
                print line
                line = ''
    
            if i == len(field_names) -1  :
                if (i+1)% columns > 0 :
                    print line
    
            i = i + 1
    
    def print_process(self):
        s           = self.sess
        columns     = 3
        line_format = self.column_format_01
    
        if len(s['proc']) == 0:
            return 0
    
        field_names = { 'pid'          : 'Process ID',
                        'spid'         : 'OS PID',
                        'program'      : 'Program',
                        'traceid'      : 'Trace ID',
                        'latchwait'    : 'Latch Wait',
                        'latchspin'    : 'Latch Spin',
                        'pga_used_mem' : 'PGA Used Mem',
                        'pga_alloc_mem': 'PGA Alloc Mem',
                      }
    
        s['proc']['program'] = s['proc']['program'].replace('.hq.navteq.com', '')

        stat_format  = '%-' + str( len( reduce(max_length, field_names.values()) )+2) + 's %-10s'
        print_fields = [ 'pid', 'spid', 'program', 'traceid', 'latchwait', 'latchspin', 'pga_used_mem', 'pga_alloc_mem' ]
        line         = ''
        i            = 0

        for j in print_fields:
            if i == 0:
                print ''
                print '-- Process ' + self.delimiter

            if j is not None:
                stat = stat_format % ( field_names[j] + ': ' , str(s['proc'][j]) )
            else:
                stat = ' '

            line = line + line_format % ( stat, ' ' )
    
    
            if (i+1)% columns  == 0:
                print line
                line = ''
    
            if i == len(field_names) -1  :
                if (i+1)% columns > 0 :
                    print line
    
            i = i + 1
      
   
    def print_sess_longop(self):
        s           = self.sess
        columns     = 3
        line_format = self.column_format_01
   
        if len(s['sess_longop']) == 0:
            return 0
   
        field_names = { 'sid'           : 'SID',
                        'serial#'       : 'Serial#',
                        'opname'        : 'Operation',
                        'target'        : 'Target',
                        'sofar'         : 'So Far',
                        'totalwork'     : 'Total Work',
                        'units'         : 'Units',
                        'time_remaining': 'Time Remain.',
                        'sql_address'   : 'SQL Address',
                        'sql_id'        : 'SQL ID',
                        'work'          : 'Work'
                      }
  
        s['sess_longop']['work'] = str(s['sess_longop']['sofar']) + '/' + str(s['sess_longop']['totalwork']) + ' ' + s['sess_longop']['units']
        s['sess_longop']['time_remaining'] = str(s['sess_longop']['time_remaining']) + ' sec.'
 
        stat_format  = '%-' + str( len( reduce(max_length, field_names.values()) )+2) + 's %-10s'
        print_fields = [ 'sid', 'opname', 'target', 'work', 'time_remaining', 'sql_id' ]
        line         = ''
        i            = 0

        for j in print_fields:
            if i == 0:
                print ''
                print '-- Sess. LongOps ' + self.delimiter

            if j is not None:
                stat = stat_format % ( field_names[j] + ': ' , str(s['sess_longop'][j]) )
            else:
                stat = ' '

            line = line + line_format % ( stat, ' ' )
   
   
            if (i+1)% columns  == 0:
                print line
                line = ''
   
            if i == len(field_names) -1  :
                if (i+1)% columns > 0 :
                    print line
   
            i = i + 1


    def lock_snapshot(self, run, SID):
        if run == 1:
            self.sess['lock'] = {}
        if run == 2:
            cursor = self.db.cursor()
            fields = '  addr, id1, id2, lmode, type , request, object_type, object_name '
            sql_stmt = 'select distinct ' + fields + " \
                        from ( select distinct a.inst_id, a.sid, ltrim(a.addr, '0') addr, a.kaddr, replace(replace(b.id1_tag, '0 or '), ' ', '_') || '=' || id1 id1, \
                        replace(replace(decode(nvl(b.id2_tag, 'id2'), '0', 'id2', '1', 'id2', '0/1', 'id2', b.id2_tag), '0 or '), ' ', '_') || '=' || id2 id2, \
                        decode(lmode, 0, '0/None', \
                        1, '1/Null', \
                        2, '2/Row-S (SS)', \
                        3, '3/Row-X (SX)', \
                        4, '4/Share (S)', \
                        5, '5/S/Row-X (SSX)', \
                        6, '6/Exclusive (X)', \
                        lmode || '/??') lmode, \
                        a.type || ' - ' || b.name type, \
                        decode(a.request, 0, '0/None', \
                        1, '1/Null', \
                        2, '2/Row-S (SS)', \
                        3, '3/Row-X (SX)', \
                        4, '4/Share (S)', \
                        5, '5/S/Row-X (SSX)', \
                        6, '6/Exclusive (X)', \
                        a.request || '/ ??' ) request, \
                        a.ctime/60 ctime, \
                        a.block, \
                        b.description, \
                        c.object_type, c.object_name \
                        from gv$lock a, v$lock_type b , dba_objects c \
                        where a.type = b.type(+) and a.id1 = c.object_id ) a \
                        where a.sid = " + SID  
            cursor.execute(sql_stmt)
            rows = cursor.fetchall()

            field_list = fields.split(',')
            s = []
            r = {}
            for j in range(0, len(rows)):
                for i in range(0, len(field_list) ):
                    r[ field_list[i].strip() ] = rows[j][i]
                s.append(r)
            self.sess['lock'] = s


    def sess_longop_snapshot(self, run, SID):
        if run == 1:
            self.sess['sess_longop'] = {}
        if run == 2:
            cursor = self.db.cursor()
            fields = 'sid, serial#, opname, target, sofar, totalwork, units, time_remaining, sql_address, sql_hash_value, sql_id'
            sql_stmt = 'select ' + fields + ' from v$session_longops where sid = ' + SID + ' and sofar != totalwork '
            cursor.execute(sql_stmt)
            rows = cursor.fetchall()

            field_list = fields.split(',')
            r = {}
            if len(rows) > 0:
                for i in range(0, len(field_list) ):
                    r[ field_list[i].strip() ] = rows[0][i]

            self.sess['sess_longop'] = r

    def proc_snapshot(self, run, SID):
        if run == 1:
            self.sess['proc'] = {}

        elif run == 2:
            cursor = self.db.cursor()
            fields = 'addr, pid, spid, username, serial#, terminal, program, traceid, latchwait, latchspin, pga_used_mem, pga_alloc_mem, pga_freeable_mem, pga_max_mem'
            sql_stmt = 'select ' + fields + ' from v$process where addr in (select paddr from v$session where sid = ' + SID + ')'
            cursor.execute(sql_stmt)
            rows = cursor.fetchall()
        
            field_list = fields.split(',')
            r = {}
            if len(rows) > 0:
                for i in range(0, len(field_list) ):
                    r[ field_list[i].strip() ] = rows[0][i]
        
            self.sess['proc'] = r
    
    
    def sql_text_snapshot(self, run, SID):
        if run == 1:
            self.sess['sql_text'] = []

        elif run == 2:
            cursor = self.db.cursor()
            sql_stmt = 'select object_name from dba_objects where object_id in (select PLSQL_ENTRY_OBJECT_ID from v$session where sid = ' + SID + ')  '
            cursor.execute(sql_stmt)
            rows = cursor.fetchall()

            r = []
            for i in range(0, len(rows) ):
                r.append(None)
                r[i] = rows[i][0]

            cursor = self.db.cursor()
            sql_stmt = 'select distinct sql_text, piece from v$sqltext where sql_id in (select sql_id from v$session where sid = ' + SID + ') order by piece' 
            cursor.execute(sql_stmt)
            rows = cursor.fetchall()
        
            for i in range(0, len(rows) ):
                r.append(None)
                r[i] = rows[i][0]
            
            self.sess['sql_text'] = r
    
    def io_snapshot(self, run, SID):
        if run == 1:
            self.sess['io'] = {}

        elif run == 2:
            cursor = self.db.cursor()
            fields = 'block_gets, consistent_gets, physical_reads, block_changes, consistent_changes'
            sql_stmt = 'select ' + fields + ' from v$sess_io where sid = ' + SID 
            cursor.execute(sql_stmt)
            rows = cursor.fetchall()
         
            field_list = fields.split(',')
            r = {}
            if len(rows) > 0:
                for i in range(0, len(field_list) ):
                    r[ field_list[i].strip() ] = rows[0][i]
        
            self.sess['io'] = r
     
    
        
    def transaction_snapshot(self, run, SID):
        if run == 1:
            self.sess['trans'] = {}

        elif run == 2:
            cursor = self.db.cursor()
            fields = 'Xidusn, Xidslot, Xidsqn, Ubafil, Ubablk, Ubasqn, Ubarec, Status, Start_Time, Start_SCN, Name, Start_Ubafil, Start_Ubablk, \
                      Start_Ubasqn, Start_Ubarec, Used_Ublk, Used_Urec, Log_IO, Phy_IO, Cr_Get, Cr_Change'
            sql_stmt = 'select ' + fields + ' from v$transaction where addr in (select taddr from v$session where sid = ' + SID + ')'
            cursor.execute(sql_stmt)
            rows = cursor.fetchall()
        
            field_list = fields.split(',')
            r = {}
            if len(rows) > 0:
                for i in range(0, len(field_list) ):
                    r[ field_list[i].strip() ] = rows[0][i]
        
            self.sess['trans'] = r
    
   
    def wait_snapshot(self, run, SID):
        if run == 1:
            self.sess['wait']               = {}

        if run == 2:
            r = {}

            cursor = self.db.cursor()
            fields = 'state, row_wait_obj#, blocking_session_status, blocking_instance, blocking_session, event, p1, p1text, p2, p2text, p3, p3text, seconds_in_wait, state, wait_time'
            sql_stmt = "select " + fields + " from v$session where sid = " + SID
            cursor.execute(sql_stmt)
            rows = cursor.fetchall()

            field_list = fields.split(',')
            for i in range(0, len(field_list) ):
                r[ field_list[i].strip() ] = rows[0][i]

            self.sess['wait'] = r


    def getDbInfo(self):
        r = {}

        cursor = self.db.cursor()
        sql_stmt = 'select version from v$instance'
        cursor.execute(sql_stmt)
        rows = cursor.fetchall()
        r['version'] = rows[0][0]
        self.sess['db_info'] = r

 
    def get_sess_info(self, SID):
        r = {}
        
        cursor = self.db.cursor()
        fields = 'saddr, paddr, taddr, sql_address, sid, serial#, username, lockwait, status, osuser, process, machine, terminal, module, program, \
                  sql_hash_value, sql_id, sql_child_number, row_wait_obj#, row_wait_row#, logon_time, last_call_et, \
                  blocking_session_status, blocking_instance, blocking_session, event, p1, p1text, p2, p2text, p3, p3text, seconds_in_wait, state, wait_time'
        sql_stmt = "select " + fields + " from v$session where sid = " + SID 
        cursor.execute(sql_stmt)
        rows = cursor.fetchall()
    
        field_list = fields.split(',')
        for i in range(0, len(field_list) ):
            r[ field_list[i].strip() ] = rows[0][i]
    

        fields = 'sysdate, instance_name, host_name'
        sql_stmt = "select " + fields + " from v$instance"
        cursor.execute(sql_stmt)
        rows = cursor.fetchall()

        field_list = fields.split(',')
        for i in range(0, len(field_list) ):
            r[ field_list[i].strip() ] = rows[0][i]
  
 
        fields = 'current_scn'
        sql_stmt = "select " + fields + " from v$database"
        cursor.execute(sql_stmt)
        rows = cursor.fetchall()

        field_list = fields.split(',')
        for i in range(0, len(field_list) ):
            r[ field_list[i].strip() ] = rows[0][i]
 
        self.sess['sess'] = r 
    
    
    def sess_metrics_snapshot(self, run, SID):
        if run == 1:
            self.sess['metric'] = {}

        elif run ==2: 
            cursor = self.db.cursor()
            fields = 'cpu, physical_reads, logical_reads, pga_memory, hard_parses, soft_parses, physical_read_pct, logical_read_pct'
            sql_stmt = "select " + fields + " from v$sessmetric where begin_time in (select max(begin_time) from v$sessmetric)  and session_id = "  + SID
        
            cursor.execute(sql_stmt)
            rows = cursor.fetchall()
       
            field_list = fields.split(',')
            r = {}
            if len(rows) > 0:
                for i in range(0, len(field_list) ):
                    r[ field_list[i].strip() ] = rows[0][i]
 
            self.sess['metric'] = r
    
    

    def sqlmonitor_snapshot(self, run, SID):
       # if self.sess['db_info']['version'].split('.')[0] == '10':
       #     return

        monitor_data = {}
        monitor_data['plan'] = []

        cursor = self.db.cursor()
        sql_stmt = "select max(sp.depth + length(spm.plan_operation) + length(spm.plan_options) + 2) \
                           from v$sql_plan_monitor spm, v$sql_plan sp where spm.sql_id = sp.sql_id and spm.sql_plan_hash_value = sp.plan_hash_value and spm.plan_line_id = sp.id and \
                           spm.sid = " + SID + "and spm.status = 'EXECUTING' "
        cursor.execute(sql_stmt)
        rows = cursor.fetchall()

        if rows[0][0] == None:
            monitor_data['max_op_length'] = 30
        else:
            monitor_data['max_op_length'] = rows[0][0] + 3


        sql_stmt = "select max(length(decode(sp.object_owner, null, ' ', sp.object_owner || '.' || sp.object_name))) \
                           from v$sql_plan_monitor spm, v$sql_plan sp where spm.sql_id = sp.sql_id and spm.sql_plan_hash_value = sp.plan_hash_value and spm.plan_line_id = sp.id and \
                           spm.sid = " + SID + "and spm.status = 'EXECUTING' "
        cursor.execute(sql_stmt)
        rows = cursor.fetchall()

        if rows[0][0] == None:
            monitor_data['max_obj_length'] = 30
        else:
            monitor_data['max_obj_length'] = rows[0][0]


        sql_stmt = "select ash.delta_time_01, ash.delta_time_02, ash.rd_io_bytes, ash.wr_io_bytes, ash.total_io_bytes  \
                           from v$sql_plan_monitor spm, \
                                (select a.sql_exec_start, a.sql_exec_id, sum(a.tm_delta_time) delta_time_01, sum(a.delta_time) delta_time_02,  \
                                        sum(a.delta_read_io_bytes) rd_io_bytes, sum(a.delta_write_io_bytes) wr_io_bytes, sum(a.delta_read_io_bytes)+sum(a.delta_write_io_bytes) total_io_bytes \
                                 from  v$active_session_history a \
                                 where a.session_id = " + SID + " group by  a.sql_exec_start, a.sql_exec_id )  ash \
                           where spm.sql_exec_start = ash.sql_exec_start(+) and spm.sql_exec_id = ash.sql_exec_id(+) and \
                                 spm.sid = " + SID + "and spm.status = 'EXECUTING' "

        cursor.execute(sql_stmt)
        rows = cursor.fetchall()


        try:
            monitor_data['delta_tm_01'] = rows[0][0]
        except:
            monitor_data['delta_tm_01'] = 1

        try:
            monitor_data['delta_tm_02'] = rows[0][1]
        except:
            monitor_data['delta_tm_02'] = 1

        try:
            monitor_data['total_rd_io_bytes'] = rows[0][2]
        except:
            monitor_data['total_rd_io_bytes'] = 1

        try:
            monitor_data['total_wr_io_bytes'] = rows[0][3]
        except:
            monitor_data['total_wr_io_bytes'] = 1

        try:
            monitor_data['total_io_bytes'] = rows[0][4]
        except:
            monitor_data['total_io_bytes'] = 1


        sql_stmt = "select distinct spm.first_refresh_time,        spm.last_refresh_time,  spm.sid,             spm.sql_id,                       spm.sql_plan_hash_value, \
                           spm.plan_parent_id,            spm.plan_line_id,       \
                           lpad(' ', sp.depth) || spm.plan_operation || ' ' || spm.plan_options, \
                           decode(sp.object_name, null, '      ', decode(sp.object_owner, null, '', sp.object_owner || '.') || sp.object_name),       spm.plan_object_type, \
                           spm.plan_cost,                 sp.cardinality,   spm.plan_bytes,                            sp.time,                                           sp.cpu_cost, \
                           sp.io_cost,              sp.temp_space,    spm.output_rows,                           spm.physical_read_requests,                              spm.physical_write_requests,\
                           spm.physical_write_bytes,      nvl(spm.workarea_mem, 0),              nvl(spm.workarea_tempseg, 0) , sp.depth, sp.child_number, sp.plan_hash_value, spm.starts, \
                           ash.cpu_tm, ash.db_time, ash.rd_io_req, ash.wr_io_req, ash.rd_io_bytes, ash.wr_io_bytes, ash.int_io_bytes, ash.delta_time_01, ash.delta_time_02, spm.physical_read_bytes  \
                           from v$sql_plan_monitor spm, v$sql_plan sp, \
                                (select a.sql_exec_start, a.sql_exec_id, a.sql_plan_line_id, \
                                 sum(a.tm_delta_cpu_time) cpu_tm, sum(a.tm_delta_db_time) db_time, sum(a.delta_read_io_requests) rd_io_req, sum(a.delta_write_io_requests) wr_io_req, \
                                 sum(a.delta_read_io_bytes) rd_io_bytes, sum(a.delta_write_io_bytes) wr_io_bytes, sum(a.delta_interconnect_io_bytes) int_io_bytes, \
                                 sum(a.tm_delta_time) delta_time_01, sum(a.delta_time) delta_time_02 \
                                 from  v$active_session_history a \
                                 where a.session_id = " + SID + " group by  a.sql_exec_start, a.sql_exec_id, a.sql_plan_line_id )  ash \
                           where spm.sql_exec_start = ash.sql_exec_start(+) and spm.sql_exec_id = ash.sql_exec_id(+) and spm.plan_line_id = ash.sql_plan_line_id(+) and \
                                 spm.sql_child_address = sp.child_address and spm.sql_id = sp.sql_id and spm.sql_plan_hash_value = sp.plan_hash_value and spm.plan_line_id = sp.id and \
                                spm.sid = " + SID + "and spm.status = 'EXECUTING' \
                           order by spm.sql_id, spm.plan_line_id"


        cursor.execute(sql_stmt)
        rows = cursor.fetchall()
        for i in range(0, len(rows)):
            if i == 0:
                monitor_data['sql_id']          = rows[i][3]
                monitor_data['child_number']    = rows[i][24]
                monitor_data['plan_hash_value'] = rows[i][25]

            monitor_data['plan'].append( {
                'first_refresh_time'       : rows[i][0],
                'last_refresh_time'        : rows[i][1],
                'sid'                      : rows[i][2],
                'sql_id'                   : rows[i][3],
                'sql_plan_hash_value'      : rows[i][4],
                'plan_parent_id'           : rows[i][5],
                'plan_id'                  : rows[i][6],
                'plan_operation'           : rows[i][7],
                'plan_object'              : rows[i][8],
                'plan_object_type'         : rows[i][9],
                'plan_cost'                : rows[i][10],
                'plan_cardinality'         : rows[i][11],
                'plan_bytes'               : rows[i][12],
                'plan_time'                : rows[i][13],
                'plan_cpu_cost'            : rows[i][14],
                'plan_io_cost'             : rows[i][15],
                'plan_temp_space'          : rows[i][16],
                'output_rows'              : rows[i][17],
                'physical_read_requests'   : rows[i][18],
                'physical_write_requests'  : rows[i][19],
                'physical_write_bytes'     : rows[i][20],
                'workarea_mem'             : rows[i][21],
                'workarea_tempseg'         : rows[i][22], 
                'plan_depth'               : rows[i][23], 
                'starts'                   : rows[i][26],
                'cpu_tm'                   : rows[i][27],
                'db_tm'                    : rows[i][28],
                'rd_io_req'                : rows[i][29],
                'wr_io_req'                : rows[i][30],
                'rd_io_bytes'              : rows[i][31],
                'wr_io_bytes'              : rows[i][32],
                'int_io_bytes'             : rows[i][33],
                'delta_time_01'            : rows[i][34],
                'delta_time_02'            : rows[i][35], 
                'physical_read_bytes'     : rows[i][36], } )


        try:
            self.sess['old_sql_monitor'] =  self.sess['sql_monitor']
        except KeyError:
             self.sess['old_sql_monitor'] = monitor_data

        self.sess['sql_monitor'] = monitor_data 


    
    def stats_snapshot(self, run, SID):
        cursor = self.db.cursor()
        sql_stmt = "select a.statistic#, b.name, a.value from v$sesstat a, v$statname b where a.statistic# = b.statistic# and a.sid = " + SID + " order by a.statistic#  "
        #print sql_stmt
        stat_data = {}
        
        if run == 1:
            self.sess['stat']               = {}
            self.sess['stat']['delta']      = []
            self.sess['stat']['run_data']   = {}

            cursor.execute(sql_stmt)
            rows = cursor.fetchall()
            for i in range(0, len(rows)):
                self.sess['stat']['run_data'][rows[i][1]] = {}
                self.sess['stat']['run_data'][rows[i][1]]['name']   = rows[i][1]
                self.sess['stat']['run_data'][rows[i][1]]['run_01'] = rows[i][2]
    
        if run == 2:
            d = {}
            l = []
    
            cursor.execute(sql_stmt)
            rows = cursor.fetchall()
            for i in range(0, len(rows)):
                self.sess['stat']['run_data'][rows[i][1]]['run_02'] = rows[i][2]
                delta = self.sess['stat']['run_data'][rows[i][1]]['run_02'] - self.sess['stat']['run_data'][rows[i][1]]['run_01']
                self.sess['stat']['run_data'][rows[i][1]]['delta'] = delta
     
                if delta > 0:
                    d[ self.sess['stat']['run_data'][rows[i][1]]['name'] ] = self.sess['stat']['run_data'][rows[i][1]]['delta']
    
            l = sorted(d.iteritems(), key=operator.itemgetter(1))
            self.sess['stat']['delta'] = l
    
    
    def events_snapshot(self, run, SID):
        cursor = self.db.cursor()
        sql_stmt = "select event_id, event, time_waited_micro from v$session_event where wait_class not in ('Idle') and sid = " + SID + " order by event_id"
        event_data = {}
    
        if run == 1:
            self.sess['event']              = {}
            self.sess['event']['delta']     = []
            self.sess['event']['run_data']  = {}

            cursor.execute(sql_stmt)
            rows = cursor.fetchall()
            for i in range(0, len(rows)):
                self.sess['event']['run_data'][rows[i][1]] = {}
                self.sess['event']['run_data'][rows[i][1]]['name']   = rows[i][1]
                self.sess['event']['run_data'][rows[i][1]]['run_01'] = rows[i][2]
    
        if run == 2:
            d = {}
            l = []
    
            cursor.execute(sql_stmt)
            rows = cursor.fetchall()
            for i in range(0, len(rows)):
                try:
                    self.sess['event']['run_data'][rows[i][1]]['run_02'] = rows[i][2]
                except KeyError:
                    self.sess['event']['run_data'][rows[i][1]] = {}
                    self.sess['event']['run_data'][rows[i][1]]['name']   = rows[i][1]
                    self.sess['event']['run_data'][rows[i][1]]['run_01'] = 0
                    self.sess['event']['run_data'][rows[i][1]]['run_02'] = rows[i][2]

                delta = self.sess['event']['run_data'][rows[i][1]]['run_02'] - self.sess['event']['run_data'][rows[i][1]]['run_01']
                self.sess['event']['run_data'][rows[i][1]]['delta'] = delta
    
                if delta > 0:
                    d[ self.sess['event']['run_data'][rows[i][1]]['name'] ] = self.sess['event']['run_data'][rows[i][1]]['delta']
    
            l = sorted(d.iteritems(), key=operator.itemgetter(1))
            self.sess['event']['delta']=l

    def segstat_snapshot(self, run, SID):
        cursor = self.db.cursor()
        sql_stmt = "select statistic#, b.object_name || ' (' || b.object_type || ') - ' ||  statistic_name, value from v$segstat a, dba_objects b " + \
                   " where a.obj# = b.object_id and b.owner in (select username from v$session where sid = " + SID + ")"
        segstat_data = {}

        if run == 1:
            self.sess['segstat']              = {}
            self.sess['segstat']['delta']     = []
            self.sess['segstat']['run_data']  = {}

            cursor.execute(sql_stmt)
            rows = cursor.fetchall()
            for i in range(0, len(rows)):
                self.sess['segstat']['run_data'][rows[i][1]] = {}
                self.sess['segstat']['run_data'][rows[i][1]]['name']   = rows[i][1]
                self.sess['segstat']['run_data'][rows[i][1]]['run_01'] = rows[i][2]

        if run == 2:
            d = {}
            l = []

            cursor.execute(sql_stmt)
            rows = cursor.fetchall()
            for i in range(0, len(rows)):
                try:
                    self.sess['segstat']['run_data'][rows[i][1]]['run_02'] = rows[i][2]
                except KeyError:
                    self.sess['segstat']['run_data'][rows[i][1]]           = {}
                    self.sess['segstat']['run_data'][rows[i][1]]['run_01'] = 0
                    self.sess['segstat']['run_data'][rows[i][1]]['run_02'] = rows[i][2]

                delta = self.sess['segstat']['run_data'][rows[i][1]]['run_02'] - self.sess['segstat']['run_data'][rows[i][1]]['run_01']
                self.sess['segstat']['run_data'][rows[i][1]]['delta'] = delta

                if delta > 0:
                    d[ self.sess['segstat']['run_data'][rows[i][1]]['name'] ] = self.sess['segstat']['run_data'][rows[i][1]]['delta']

            l = sorted(d.iteritems(), key=operator.itemgetter(1))
            self.sess['segstat']['delta']=l



def format_string(s):
    if s == None:
        return ' '

    return str(s)



def format_number(n, unit=1000):
    if n == None:
        return '0'


    length = len(str(n))

    if length > 13:
        return str(n/unit/unit/unit/unit) + 'P'
    elif length > 10:
        return str(n/unit/unit/unit) + 'G'
    elif length > 7:
        return str(n/unit/unit) + 'M'
    elif length > 4:
        return str(n/unit) + 'K'
    else:
        return str(n)



#########################
##
## main()
##
##############################
if __name__ == '__main__':
    main()


