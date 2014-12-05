sga="/Users/ed/Projects/sga"
user="ubuntu"
ip="shelleygodwinarchive.org"
host="shelleygodwinarchive.org"
ids=(a b c1 c2)

for id in ${ids[*]}
do
    tei="$sga/data/tei/ox/ox-frankenstein_notebook_$id.xml"
    echo "generating Manifest.jsonld for $tei"
    bin/unbind $tei http://$host/data/ox/ox-frankenstein-notebook_$id/Manifest.jsonld > Manifest.jsonld
    echo "deploying Manifest.jsonld to $ip"
    scp Manifest.jsonld $user@$ip:/usr/share/nginx/static/data/ox/ox-frankenstein-notebook_$id/
done
