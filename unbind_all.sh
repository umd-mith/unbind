#!/bin/bash
sga="/home/rviglian/Projects/sga"
ids=(ox-ms_abinger_c56 ox-ms_abinger_c57 ox-ms_abinger_c58 \ 
        ox-frankenstein_notebook_a ox-frankenstein_notebook_b ox-frankenstein_notebook_c1 ox-frankenstein_notebook_c2 \
	ox-frankenstein-volume_i ox-frankenstein-volume_ii ox-frankenstein-volume_iii \
	ox-ms_shelley_e1 ox-ms_shelley_e2 ox-ms_shelley_e3 \ 
	ox-prometheus_unbound-act_i ox-prometheus_unbound-act_ii ox-prometheus_unbound-act_iii ox-prometheus_unbound-act_iv \
	ox-ion ox-ode_to_heaven ox-misery_e2_draft ox-misery_e2_fair)

mkdir $sga/site/manifests/ox

for id in ${ids[*]}
do
    tei="$sga/data/tei/ox/$id.xml"
    echo "generating Manifest.jsonld for $tei"
    bin/unbind $tei http://shelleygodwinarchive.org/manifests/ox/$id/Manifest.jsonld > Manifest.jsonld
    echo "moving Manifest.jsonld to static site"
    mkdir $sga/site/manifests/ox/$id
    mv Manifest.jsonld $sga/site/manifests/ox/$id/
    echo "generating Manifest-index.jsonld for $tei"
    bin/unbind --skip-annos $tei http://shelleygodwinarchive.org/manifests/ox/$id/Manifest-index.jsonld > Manifest-index.jsonld
    echo "copying Manifest-index.jsonld to static site"
    mv Manifest-index.jsonld $sga/site/manifests/ox/$id/
done
