            +-----------+
            |Data Source|
            +--^--+-----+
               |  |
+-------+    +-+--v--+    +-------+
|Trigger+---->Fetcher+---->Storage|
+-------+    +-------+    +-^--+--+
                            |  |
                         +--+--v--+
                         |Showcase|
                         +----+---+
                              |
                         +----+------+
                         | User view |
                         +-----------+

----------------------------------------------------------------------

                  +-----------+
                  |Data Source|
                  +--^--+-----+
                     |  |
                 +-----------------------------+
                 |   |  |       Git Repository |
+----------------------------+                 |
| +-----------+  |   |  |    |                 |
| |on:        |  | +-+--v--+ | +-----------+   |
| |  schedule:+---->main.py+--->.json,.csv |   |
| |  - cron   |  | +-------+ | +----+------+   |
| +--+--------+  |           |      |          |
|                |           | +------------+  |
| GitHub Actions |           | | .html,.js  |  |
+----------------------------+ +----+-------+  |
                 |                  |          |
                 +-----------------------------+
                                    |
                                +---v----------+
                                | GitHub Pages |
                                +--------------+
                                
Check out https://cxumol.github.io/LongRiver/ for demonstration

Read https://xirtam.cxumol.com/long-river-station-data-get-plot/ for technical description in Chinese.
         
