function getDeps(){
    echo "$(apt show ${1} 2>/dev/null  | grep -P "Depends: " | sed 's~Depends:~~g;s~(~~g;s~)~~g;s~>~~g;s~<~~g' |tr -d " \t\n\r" | tr "," "\n")"
}

aptStr=$(dpkg-deb -I $1 | grep -P "Depends: " | sed 's~Depends:~~g;s~(~~g;s~)~~g;s~>~~g;s~<~~g' | tr -d " \t\n\r" | tr "," "\n")
for item in $aptStr; do 
    aptStr+="\n$(getDeps ${item})"
done 
echo -e "${aptStr}" | awk '!a[$0]++' > /tmp/aptStr