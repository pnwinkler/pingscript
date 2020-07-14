# pingscript
Logs and archives ping results on a Linux system. I suggest setting parameters at the top of the file, then running once from terminal to ensure it functions as expected.

Intended use: as a cron job. Example line in crontab (substitute your path):  
*/2 15-23 * * * python3.8 /home/you/path/to/pingscript.py

Suggested extras: Append tail pingtimes to your ~/.bash_aliases, or a combined ping.  
alias tpt="tail ~/Desktop/pingtimes"  
alias cbp="tail ~/Desktop/pingtimes; sleep 4; ping google.com | grep -P -o '([0-9]+ ms)|([0-9]+\.\d* ms)'"

More specifically, this program logs the date, min/avg/max/mdev ping results and whether a VPN was active or not to one line each time it is called. On the first of each month, it names and archives the written to file and starts on a new file. This provides a historical record of your networks health.
