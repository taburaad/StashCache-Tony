while getopts "t:f:d:s:p:" opt; do
  case "$opt" in
      t) timeout=$OPTARG ;;
      f) file=$OPTARG ;;
      d) diff=$OPTARG ;;
      s) expSize=$OPTARG ;;
      p) xpid=$OPTARG ;;
  esac
done
shift $((OPTIND-1))


start_watchdog(){
    timeout="$1"
    file="$2"
    diff="$3"
    expSize="$4"
    xpid="$5"
    prevSize=0
    newSize=0
    while (( newSize<expSize ))
    do 
        sleep $timeout #check status after every x seconds
        if [ -e $file ]; then
            newSize=$(du -b $file | cut -f1)
            nextSize=$((prevSize+diff))
            wantSize=$((nextSize<expSize?nextSize:expSize))
            if [ $newSize -eq $expSize ]; then
                #finished
                exit 0
            fi
            if [ $newSize -lt $wantSize ]; then #if time out
                echo "killing process after timeout of $timeout seconds"
                if ps -p $xpid > /dev/null
                then
                    #xrdcp running, kill xrdcp now
                    kill -9 $xpid
                else
                    #xrdcp already aborted on its own, use xrdcp exit code
                    xrdcp_abort=$?
                    exit $xrdcp_abort
                fi
                
            else #if file increases accordingly
                prevSize=$(du -b $file | cut -f1)
            fi
        else
            #file does not exist (timeout)
            if ps -p $xpid > /dev/null
            then
                #xrdcp running, killing now
                kill -9 $xpid
            else
               #xrdcp not running, use xrdcp exit code
                xrdcp_abort=$?
                exit $xrdcp_abort
            fi
        fi
    done
    
    
}

start_watchdog "$timeout" "$file" "$diff" "$expSize" "$xpid" &
watchdog_pid=$!
"$@"
cp_exit=$?
# If the cp command exits, kill the watchdog
kill $watchdog_pid
exit $cp_exit
