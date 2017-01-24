#!/bin/bash
sga="/home/rviglian/Projects/sga"
ids=(ox/ox-ms_abinger_c56 ox-ms_abinger_c57 ox-ms_abinger_c58 \ 
    ox/ox-frankenstein_notebook_a ox/ox-frankenstein_notebook_b ox/ox-frankenstein_notebook_c1 ox/ox-frankenstein_notebook_c2 \
	ox/ox-frankenstein-volume_i ox/ox-frankenstein-volume_ii ox/ox-frankenstein-volume_iii \
	ox/ox-ms_shelley_e1 ox/ox-ms_shelley_e2 ox/ox-ms_shelley_e3 \ 
	ox/ox-prometheus_unbound-act_i ox/ox-prometheus_unbound-act_ii ox/ox-prometheus_unbound-act_iii ox/ox-prometheus_unbound-act_iv \
	ox/ox-ion ox/ox-ode_to_heaven ox/ox-misery_e2_draft ox/ox-misery_e2_fair \
    bl/bl-loan_ms_70_08 bl/bl-upon_the_wandering_winds bl/bl-to_laughter bl/bl-hymn_to_intellectual_beauty bl/bl-mont_blanc)

mkdir $sga/site/manifests

for id in ${ids[*]}
do
    tei="$sga/data/tei/$id.xml"
    echo "generating Manifest.jsonld for $tei"
    bin/unbind $tei http://shelleygodwinarchive.org/manifests/$id/Manifest.jsonld > Manifest.jsonld
    echo "moving Manifest.jsonld to static site"
    mkdir $sga/site/manifests/$id
    mv Manifest.jsonld $sga/site/manifests/$id/
    echo "generating Manifest-index.jsonld for $tei"
    bin/unbind --skip-annos $tei http://shelleygodwinarchive.org/manifests/$id/Manifest-index.jsonld > Manifest-index.jsonld
    echo "copying Manifest-index.jsonld to static site"
    mv Manifest-index.jsonld $sga/site/manifests/$id/
done
