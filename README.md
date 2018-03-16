# SessSnap

SessSnap is an Oracle session monitoring utility to track user level evnts, statistics, and execution plans.


## Getting Started

To get started, clone the repo:

```
https://github.com/tongelja/sess_snap.git
```



### Prerequisites

You will need to have cx_Oracle installed.


## Running RacSnap


Run SessSnap with python2 (python3 update coming soon) and pass your connection information and you session ID.

```
python sesssnap.py -s 1011 -c mydb001:myserver00001:sys;mysyspassword
```

Your output will refresh every few seconds and look like this:

```
-- Session -----------------------------
Date:          2018-03-16 16:01:13              Host:          myserver00001                    Instance:      mydb00001                        Cur SCN:       1560912771824
SID, Serial#:  (1011, 49177)                    Username:      MYUSER_1801                      Logon Time:    2018-03-16 15:43:10              Last Call ET:  200
Clnt OS User:  myuser                           Clnt Host:     patlmapbat21.lnx.in.here.com     Clnt Module:   no app name    : myuser          SQL ID:        5u2v8ah38ymmy
Sess Addr:     000000045A84A698                 Proc Addr:     000000045DBFE3C0                 Tran Addr:     000000044724C5A0                 SQL Addr:      00000003B476EE00
SQL Child#:    3                                Status:        ACTIVE                           Blk Session:   None

-- Transaction -----------------------------
Undo Seg Num:    130                            Undo Slot Num:   32                             Undo Seq Num:    3138
UBA File:        5                              UBA Block:       728857                         UBA Seq#:        599                            UBA Rec#:        18
Strt UBA File:   5                              Strt UBA Block:  309815                         Strt UBA Seq#:   589                            Strt UBA Rec#:   11
Logical I/O:     1021545                        Physical I/O:    4872873                        Cons Gets:       94687249                       Cons Changes:    427476
Status:          ACTIVE                         Strt Time:       03/16/18 15:43:09              Strt SCN:        1560912180982
Undo Blks Used:  9569                           Undo Rcds Used:  189282

-- Sess I/O -----------------------------
Block Gets:      402418                         Cons. Gets:      94687343                       Physical Reads:  4822738
Block Changes:   619134                         Cons. Changes:   427476

-- Wait Event -----------------------------
Event:  resmgr:cpu quantum
PText:  location=3, consumer group id=17380,  =0
State:  On CPU (Previous wait event listed)

-- SQL Text (5u2v8ah38ymmy) -----------------------------
select * from my_table where id in (select id from TEMP_ID) order by id 

-- Statistics -----------------------------
Statistic                                                              Delta                 Rate
physical read bytes                                              111730688.0      22346137.0 /Sec
cell physical IO interconnect bytes                              118784000.0      23756800.0 /Sec
session pga memory                                               141033472.0      28206694.0 /Sec
session uga memory                                               141152288.0      28230457.0 /Sec
logical read bytes from cache                                   1802780672.0     360556134.0 /Sec

-- Events -----------------------------
Event                                                                  Delta                 Rate
direct path write temp                                                8622.0          1724.0 /Sec
cell multiblock physical read                                        96121.0         19224.0 /Sec
resmgr:cpu quantum                                                  202550.0         40510.0 /Sec
cell single block physical read                                     232084.0         46416.0 /Sec
cell list of blocks physical read                                   790008.0        158001.0 /Sec

-- SQL Monitor -----------------------------
SQL ID           : 04fvn7y0t6w1m
Child Number     : 4
Plan Hash Value  : 706530942
                                                                                                   Est    Act            Est IO  PhyRd PhyWrt PhyWrt  PhyRd     Est
ID   Operation                                   Object                                           Rows   Rows    Exe       Cost    Req    Req  Bytes  Bytes    Temp    Mem   Temp  CPU%  IO%
--   ---------                                   ------                                           ----   ----    ---       ----  ----- ------ ------  -----    ----    ---   ----  ----  ---
0    SELECT STATEMENT                                                                                0    200      1          0      0      0      0      0       0      0      0
1     SORT ORDER BY                                                                              2739K    200      1        51K      0      0      0      0    147M  2314K      0
2      NESTED LOOPS                                                                              2739K    43K      1        24K      0      0      0      0       0      0      0
3       NESTED LOOPS                                                                             2739K    43K      1        24K      0      0      0      0       0      0      0
4        SORT UNIQUE                                                                             1224K  2794K      1        481    163    161    32M    32M       0      0      0    13   18
5         TABLE ACCESS STORAGE FULL              MYUSER_1801.TEMP_LINK                           1224K  2794K      1        481     38      0      0    36M       0      0      0     4    0
6        INDEX RANGE SCAN                        MYUSER_1801.NX_NAMEDPLACELINK_LINKID                2    43K  2835K          1    14K      0      0   122M       0      0      0    25   72
7       TABLE ACCESS BY INDEX ROWID              MYUSER_1801.NT_NAMED_PLACE_LINK                     2    43K    50K          1   2441      0      0    19M       0      0      0     6    8
0    SELECT STATEMENT                                                                                0    200      1          0      0      0      0      0       0      0      0            <<-- -1%
1     SORT ORDER BY                                                                              5945K    200      1       146K      0      0      0      0    387M   538M      0    16   81 <<-- -9%
2      NESTED LOOPS                                                                              5945K  9228K      1        79K      0      0      0      0       0      0      0         81 <<-- -1%
3       NESTED LOOPS                                                                             6124K  9228K      1        79K      0      0      0      0       0      0      0     6   32 <<-- -1%
4        VIEW                                                                                    1224K  2794K      1       5873      0      0      0      0       0      0      0            <<-- -1%
5         HASH UNIQUE                                                                            1224K  2794K      1       5873      0      0      0      0     23M      0      0    13   19 <<-- 109%
6          TABLE ACCESS STORAGE FULL             MYUSER_1801.TEMP_LINK                           1224K  2794K      1        481      0      0      0      0       0      0      0
7        INDEX RANGE SCAN                        MYUSER_1801.PK_SHAPE_POINT_LINKID_SEQUENCE          5  9228K  3093K          1    87K      0      0   684M       0      0      0   142  571 <<-- -1%
8       TABLE ACCESS BY INDEX ROWID              MYUSER_1801.NT_SHAPE_POINT                          5  9228K    11M          1   880K      0      0  6900M       0      0      0   507 2488 <<-- -1%

```




## Authors

* **John Tongelidis** - *Initial work* - [tongelja](https://github.com/tongelja)
