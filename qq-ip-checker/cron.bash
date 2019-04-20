source ~/dev/pyv-env/bin/activate

cd ~/dev/chord-data/qq-ip-checker

python3 checker.py

deactivate

if [ "$(ls -l qq-ips.txt | cut -f5 -d' ')" != "0" ]
then
    git add qq-ips.txt
    git commit -m 'Update'
    git push -u
fi
