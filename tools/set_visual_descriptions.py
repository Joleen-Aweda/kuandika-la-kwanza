#!/usr/bin/env python3
"""Apply visually verified, concrete Kiswahili descriptions to actual visuals."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DESCRIPTIONS = {
    "pg001_im001": "Picha inaonesha saini ya Dkt. Lyabwene M. Mtahabwa kwa wino wa bluu juu ya usuli wa kijani hafifu, na jina lake limechapishwa kwa herufi nyeusi chini ya saini.",
    "pg006_im001": "Picha inaonesha msimbo wa QR wa miraba myeusi na meupe. Katikati yake kuna nembo ndogo yenye mchoro wa mtoto anayesoma; msimbo huu unaelekeza kwenye maktaba mtandao.",
    "pg007_im003": "Mchoro unaonesha mstari mweusi wa mazoezi wenye maumbo ya U yanayojirudia. Kila umbo lina mistari miwili ya wima inayoshuka na kuunganishwa na tao la mviringo chini.",
    "pg007_im004": "Mchoro unaonesha mstari wa mazoezi wenye maumbo ya ngazi za mstatili yanayojirudia, yakipanda kwa mstari wa wima na kuendelea kwa mstari mfupi wa mlalo.",
    "pg007_im005": "Mchoro unaonesha matao meusi yanayojirudia kama herufi m ndogo, kila tao likipanda na kushuka hadi kwenye mstari wa chini.",
    "pg007_im006": "Mchoro unaonesha mstari wa zigizagi wenye pembetatu nyingi zinazojirudia, ukiwa na ncha kali zinazopanda na kushuka kwa mpangilio mmoja.",
    "pg008_im001": "Picha inaonesha samaki wa kufuatisha kwa mistari ya nukta. Samaki ana mwili mpana, jicho moja, pezi tatu na mkia wenye ncha mbili.",
    "pg008_im002": "Picha inaonesha paka aliyeketi, aliyechorwa kwa mistari ya nukta. Ana masikio mawili yenye ncha, masharubu, miguu minne na mkia mrefu uliopinda juu.",
    "pg008_im003": "Picha inaonesha kaptula ya kufuatisha kwa mistari ya nukta, yenye mkanda mpana kiunoni na sehemu mbili za miguu zilizotenganishwa katikati.",
    "pg008_im006_crop_v1": "Picha inaonesha sketi ya kufuatisha kwa mistari ya nukta, yenye mkanda mpana kiunoni na mikunjo minne mirefu inayoshuka hadi kwenye pindo.",
    "pg009_im001_crop_v1": "Mchoro namba moja unaonesha kaptula nyeupe yenye mpaka mweusi, mkanda mpana wa kiunoni na sehemu mbili za miguu.",
    "pg009_im002_crop_v1": "Mchoro namba mbili unaonesha sketi nyeupe yenye mpaka mweusi, mkanda wa kiunoni na mikunjo minne mirefu inayopanuka kuelekea chini.",
    "pg009_im003_crop1": "Mchoro namba nne unaonesha chupa ndefu isiyo na kifuniko, yenye shingo nyembamba, mabega yaliyopinda na sehemu ya chini ya mviringo.",
    "pg009_im006_crop1": "Mchoro namba tatu unaonesha kikombe kikubwa cha mviringo chenye mpini mmoja upande wa kulia na mdomo mpana juu.",
    "pg009_im007_crop_v1": "Mchoro namba tano unaonesha kiti cha mbao kwa mtazamo wa pembeni, chenye mgongo mrefu, sehemu ya kukalia na miguu minne.",
    "pg009_im009_crop1": "Mchoro namba sita unaonesha meza ya mstatili kwa mtazamo wa pembeni, yenye sehemu tambarare ya juu na miguu minne mirefu.",
    "pg010_im001": "Mchoro unaonesha safu tano za mistari ya nukta ya kufuatisha: mawimbi mapana, zigizagi kubwa, zigizagi ndogo, nusu duara zinazoelekea juu, na matao madogo yanayojirudia.",
    "pg014_im005_crop_v1_crop1": "Mchoro unaonesha herufi ndogo u nyeusi na hatua nne za kuiandika. Mishale yenye namba moja hadi nne inaonesha kushuka, kupinda chini, kupanda na kumalizia kwa mkia mfupi kulia.",
    "pg015_im001": "Picha inaonesha ua jekundu aina ya hibiskasi lenye petali kubwa, chavua ndefu inayoning'inia upande wa kushoto, shina la kijani na majani matatu ya kijani.",
    "pg016_im001": "Picha inaonesha sungura mweupe wa katuni akiruka kwa furaha. Ana masikio marefu yenye rangi ya waridi ndani, amevaa fulana ya zambarau na suruali ya machungwa, na ameinua mikono yote miwili.",
    "pg018_im001": "Picha inaonesha babu mwenye ngozi ya kahawia akitembea kwa kujiegemeza kwenye fimbo. Amevaa kofia ya bluu, koti jeusi, shati jeupe, suruali ya kahawia na viatu vyeusi.",
    "pg018_im002": "Picha inaonesha bibi mwenye ngozi ya kahawia akisimama kwa kujiegemeza kwenye fimbo ndefu. Amevaa hijabu ya machungwa, blauzi ya kijani na sketi ya bluu yenye duara kubwa za rangi mbalimbali.",
    "pg018_im003": "Picha inaonesha buibui mweusi na kahawia akiwa katikati ya utando mkubwa wa nyuzi nyeusi. Utando una mistari inayotoka katikati na miduara isiyo sawa inayouzunguka.",
    "pg019_im005_crop1_crop1_crop1": "Picha inaonesha bao la mbao la rangi ya kahawia lenye safu nne za mashimo madogo ya mviringo. Mbegu nyingi nyeusi na kahawia zimetawanyika upande wa kulia wa bao.",
    "pg019_im007_crop_v1": "Mchoro unaonesha herufi ndogo m nyeusi na mishale sita yenye namba. Mishale inaelekeza mstari wa kwanza kushuka, kisha matao mawili kupanda na kushuka, na mkia kuishia upande wa kulia.",
    "pg020_im001": "Picha inaonesha kipande kimoja cha muwa wa kijani-kijano, kikiwa kirefu, cha mviringo na chenye vifundo vinavyoonekana katika sehemu kadhaa.",
    "pg020_im002": "Picha inaonesha uma wa chuma wa rangi ya fedha, wenye mpini mrefu uliopinda kidogo na meno manne marefu upande wa juu.",
    "pg020_im003": "Picha inaonesha bustani yenye maua mengi ya rangi ya zambarau, waridi, njano na nyekundu. Maua makubwa yana vitovu vya njano na yamezungukwa na majani na nyasi za kijani.",
    "pg022_im001": "Picha inaonesha kobe wa rangi ya kahawia akitembea kuelekea kushoto. Ana gamba kubwa lenye vipande vya mstatili, kichwa kidogo, miguu minne yenye kucha na mkia mfupi.",
    "pg022_im002": "Picha inaonesha kuku jike wa rangi ya kahawia na manjano akisimama kwa miguu miwili. Ana upanga mwekundu kichwani, mdomo mfupi na manyoya meusi mkiani.",
    "pg022_im003": "Picha inaonesha kaa wa rangi ya kijivu-zambarau, mwenye gamba pana la mviringo, miguu minane iliyopinda na makucha mawili makubwa mbele.",
    "pg022_im004": "Picha inaonesha keki ya duara yenye tabaka jeupe, ikiwa juu ya sahani nyeupe. Juu yake kuna krimu ya waridi inayotiririka kwa matone pembeni.",
    "pg023_im022_crop1": "Picha inaonesha dumu la plastiki la rangi ya njano, lenye umbo la mstatili, pembe zilizopinda, mpini juu na kifuniko kidogo chekundu.",
    "pg026_im001": "Picha inaonesha jedwali la zoezi lenye nguzo tatu: Konsonanti, Irabu na Silabi. Mfano wa kwanza unaunganisha m na a kupata ma; mistari inayofuata ina k na o, n na u, b na i, d na a, na m na e pamoja na nafasi za kujaza.",
    "pg028_im001": "Picha inaonesha mvulana mwenye ngozi ya kahawia na nywele nyeusi akilia. Macho yake yamefumba, mdomo umefunguka na machozi mengi yanatiririka mashavuni; amevaa shati la bluu.",
    "pg028_im002": "Picha inaonesha mvulana mwenye ngozi ya kahawia amelala kitandani kwa ubavu. Kichwa chake kiko juu ya mto wa kijani, amefunikwa kwa shuka jeupe na ukuta wa chumba una rangi ya waridi.",
    "pg028_im003": "Picha inaonesha msichana mwenye ngozi ya kahawia akilima shambani kwa jembe. Ameinama kati ya mimea michanga, amevaa blauzi ya waridi na sketi ya kijani, huku milima ikionekana nyuma.",
    "pg030_im001": "Picha inaonesha taa ya kandili ya rangi ya bluu yenye fremu ya chuma na chombo cha kioo katikati. Ndani ya kioo kuna mwali mdogo wa njano na machungwa.",
    "pg030_im002": "Picha inaonesha tai ndefu ya kuvaa shingoni, yenye mistari ya ulalo ya rangi nyekundu, kijani, nyeupe na njano, pamoja na fundo jembamba juu.",
    "pg030_im003": "Picha inaonesha tikiti maji moja la kijani lenye mistari, limekatwa na kuonesha nyama nyekundu. Pembeni kuna kipande cha tikiti chenye ganda la kijani na nyama nyekundu.",
    "pg030_im004": "Picha inaonesha moto unaowaka juu ya kuni nne zilizopangwa kwa kuvukana. Miale ina rangi ya njano, machungwa na nyekundu, huku moshi mwembamba mweusi ukipanda juu.",
    "pg030_im005": "Picha inaonesha bata mwenye mwili mweupe na mabawa meusi akitembea kuelekea kushoto. Ana ngozi nyekundu kuzunguka jicho na mdomo, miguu ya njano na mkia mweusi.",
    "pg030_im006": "Picha inaonesha kiti cha mbao cha rangi ya kahawia, chenye mgongo wa mstatili, sehemu tambarare ya kukalia, miguu minne na viunzi chini.",
    "pg032_im001": "Picha inaonesha pipa kubwa la chuma la rangi ya buluu-kijivu. Lina umbo la silinda, mikanda miwili ya kuzunguka mwili na matundu mawili ya mviringo juu.",
    "pg032_im002": "Picha inaonesha popo wa rangi ya kahawia na kijivu akiruka huku mabawa yake makubwa yakiwa yamekunjuliwa. Ana masikio makubwa, macho madogo na vidole virefu ndani ya mabawa.",
    "pg032_im003": "Picha inaonesha pipi iliyofungwa kwa karatasi nyekundu yenye mistari ya njano. Ncha zote mbili za karatasi zimekunjwa na kufungwa kama vifundo.",
    "pg032_im004": "Picha inaonesha paka wa rangi ya machungwa akitembea kuelekea kulia. Ana mistari meusi mwilini, macho ya kijani, masikio yenye ncha na mkia mrefu uliopinda.",
    "pg032_im005": "Picha inaonesha pikipiki nyekundu na nyeusi yenye magurudumu mawili, taa ya mbele, vioo viwili, kiti cheusi, injini na bomba la moshi la fedha.",
    "pg032_im006": "Picha inaonesha papai moja zima lenye ganda la kijani na njano, pamoja na nusu ya papai yenye nyama ya machungwa na mbegu nyingi nyeusi katikati.",
    "pg034_im001": "Picha inaonesha saa ya mkononi yenye mkanda mwekundu wa ngozi na uso mweupe wa duara. Uso una namba nyeusi, mishale miwili na ukingo wa chuma wa rangi ya fedha.",
    "pg034_im002": "Picha inaonesha kipande cha sabuni cha rangi ya njano, chenye umbo la mstatili na pembe za mviringo, kikiwa juu ya chombo cha sabuni cha rangi ya waridi.",
    "pg034_im003": "Picha inaonesha samaki wa rangi ya kijivu na njano akielekea kushoto. Ana magamba mengi, jicho moja, mdomo mdogo, pezi za juu na chini na mkia mpana.",
    "pg034_im004_seg004_v1_crop_v1": "Picha inaonesha simu ya mkononi ya zamani yenye mwili mweusi na kijivu, skrini ya buluu, vitufe vingi vya namba na kitufe kikubwa cha mviringo katikati.",
    "pg035_im002": "Picha inaonesha jani moja kubwa la kijani, lenye ncha kali upande wa kushoto, kikonyo upande wa kulia, mshipa mkuu katikati na mishipa midogo inayosambaa pembeni.",
    "pg035_im003": "Picha inaonesha jua jeupe linalong'aa katikati ya mwanga wa njano na bluu. Miale mirefu na mifupi inatoka kuzunguka duara la jua.",
    "pg035_im021_seg002_v1": "Picha inaonesha jiko dogo la mkaa lenye sehemu ya juu ya rangi ya kahawia na mwili mweusi-kijivu. Juu kuna vipande vya mkaa na vishikio viwili vya chuma.",
    "pg038_im001": "Picha inaonesha feni ya mezani yenye mabawa matatu ya buluu ndani ya wavu wa duara. Ina shingo, msingi wa kijivu wenye vitufe, na waya wa umeme wenye plagi upande wa kulia.",
    "pg038_im002": "Picha inaonesha fenesi moja kubwa ya kijani, yenye umbo la mviringo mrefu, ngozi yenye vinundu vidogo na kikonyo kifupi cha kahawia juu.",
    "pg038_im003": "Picha inaonesha fisi wa rangi ya kahawia akitembea kuelekea kushoto. Ana madoa mengi meusi, mgongo ulioteremka, masikio ya mviringo, miguu minne na mkia mfupi mweusi.",
    "pg039_im002_crop1": "Mchoro unaonesha herufi ndogo g nyeusi na hatua nne za kuiandika. Mishale yenye namba moja hadi nne inaonesha kuzungusha duara, kushuka kwa mstari na kupinda mkia kuelekea kushoto chini.",
    "pg040_im001": "Picha inaonesha gari jekundu kwa mtazamo wa mbele na pembeni. Lina vioo vya buluu, taa mbili, grili ya kijivu, namba ya njano na magurudumu meusi.",
    "pg040_im002": "Picha inaonesha gunia la kahawia lililojaa nafaka hadi mdomoni. Gunia limesimama wima, limekunjwa juu na lina mshono mrefu katikati.",
    "pg040_im003": "Picha inaonesha gogo la mti la rangi ya kahawia likiwa limelala kwa mlalo. Sehemu ya mbele iliyokatwa ina duara za ukuaji na upande wa juu una tawi fupi.",
    "pg040_im004": "Picha inaonesha gitaa lenye mwili wa njano-machungwa, tundu jeusi la mviringo, nyuzi sita, shingo ndefu ya kahawia na vishikio vya kurekebisha nyuzi.",
    "pg040_im005": "Picha inaonesha gauni lenye sehemu ya juu ya waridi yenye muundo wa mistari ya almasi na sketi ndefu ya njano inayopanuka na kuwa na mikunjo.",
    "pg040_im015_crop_v1_crop1": "Mchoro unaonesha herufi ndogo y yenye mishale na namba moja hadi nne upande wa kushoto, pamoja na herufi y za nukta zilizopangwa kwenye mistari ya kuandikia ili kufuatishwa.",
    "pg041_im001": "Picha inaonesha yai moja la rangi ya kahawia hafifu, lenye umbo la mviringo linalopanuka chini na kuwa jembamba juu.",
    "pg043_im001": "Picha inaonesha zeze la asili lenye chombo cha sauti cha mviringo cha rangi ya machungwa, ngozi nyeupe juu, shingo ndefu ya mbao na nyuzi kadhaa zilizofungwa.",
    "pg043_im002": "Picha inaonesha kishada cha zabibu nyingi za rangi ya zambarau, zikiwa zimeshikamana kwenye kikonyo cha kahawia chenye jani moja kubwa la kijani.",
    "pg043_im003": "Picha inaonesha zizi la mviringo lililozungushiwa uzio wa mbao. Ndani yake kuna ng'ombe wawili wa rangi ya kahawia, nyeupe na kijivu wakiwa wamesimama.",
    "pg043_im004": "Picha inaonesha zipu yenye vitambaa viwili vya buluu, meno ya dhahabu na kishikio cha dhahabu katikati; sehemu ya chini imefungwa na sehemu ya juu imeachana.",
    "pg045_im001": "Picha inaonesha hema la kijani lililosimikwa kwenye ardhi ya mchanga. Lina mlango uliofunguka mbele, dirisha dogo na kamba nne zilizofungwa ardhini kwa vigingi.",
    "pg048_im001": "Picha inaonesha raba mbili nyekundu za kuvaa miguuni, zenye kamba nyeusi, ncha nyeupe, nyayo nyeupe na mstari mweusi pembeni.",
    "pg048_im002_crop_v1": "Picha inaonesha rula ya mbao ya rangi ya kahawia yenye urefu wa sentimita ishirini. Ina alama nyeusi za vipimo na namba moja hadi ishirini.",
    "pg048_im003": "Picha inaonesha redio ya rangi ya kijivu yenye mpini na antena juu. Mbele kuna kipimo cha masafa, spika ya miraba midogo na vifundo viwili vya mviringo.",
    "pg048_im004": "Picha inaonesha reli mbili nyeusi za chuma zikielekea mbali, zikiwa zimeunganishwa na vipande vingi vya mlalo juu ya mawe ya kahawia na kijivu.",
    "pg050_im006": "Mchoro unaonesha herufi ndogo v nyeusi na hatua tatu za kuiandika. Mishale yenye namba moja na mbili inashuka na kupanda kuunda pembe, kisha mshale wa tatu unamalizia kwa mkia mfupi kulia.",
    "pg051_im001": "Picha inaonesha viatu viwili vyeusi vya kufungwa kwa mkanda, vyenye sehemu za ndani za kijani-kijivu na nyayo nyeusi bapa.",
    "pg051_im002": "Picha inaonesha kiti cha mbao cha rangi ya kahawia, chenye mgongo wa mstatili, sehemu ya kukalia, miguu minne na viunzi vya chini.",
    "pg051_im003_crop_v1": "Picha inaonesha vikapu viwili vikubwa vya kusuka vya rangi ya kahawia. Kila kikapu kina umbo pana linalopanuka juu na vipini viwili vya mviringo.",
    "pg051_im004": "Picha inaonesha ngoma ya mbao ya rangi ya kahawia, yenye umbo la kikombe, ngozi ya mviringo juu na mkanda mwekundu unaozunguka sehemu ya katikati.",
    "pg051_im005": "Picha inaonesha vijiko vitano vya chuma vya rangi ya fedha, vikiwa vimepangwa kwa kuvukana na kila kimoja kikiwa na bakuli la mviringo na mpini mrefu.",
    "pg051_im006": "Picha inaonesha lundo la viazi vingi vya rangi ya kahawia hafifu, vyenye maumbo ya mviringo yasiyo sawa na madoa madogo kwenye maganda.",
    "pg053_im001": "Picha inaonesha chui wa rangi ya kahawia ya dhahabu mwenye madoa mengi meusi ya mviringo. Amesimama kwa miguu minne, ana meno yanayoonekana na mkia mrefu uliopinda.",
    "pg053_im002": "Picha inaonesha chura wa rangi ya kahawia na kijivu akiwa ameketi kwa miguu ya nyuma iliyokunjwa. Ana ngozi yenye madoadoa, jicho kubwa la mviringo na vidole virefu.",
    "pg053_im003": "Picha inaonesha chaja nyeusi ya simu yenye plagi ya pini tatu. Ina waya mrefu mweusi uliojikunja na kiunganishi kidogo mwisho wa waya.",
    "pg053_im004": "Picha inaonesha chupa ya plastiki ya buluu hafifu iliyojaa maji, yenye mwili wenye mistari ya kushika, shingo nyembamba na kifuniko cha skrubu kilichofungwa.",
    "pg054_im002_crop1": "Picha inaonesha sungura mweupe wa katuni aliyevaa fulana ya zambarau na suruali ya machungwa, akiwa chini ya kisanduku cha maelekezo chenye mpaka wa waridi kuhusu kutazama video na kuandika herufi.",
    "pg060_im002": "Mchoro unaonesha herufi kubwa O nyeusi na hatua mbili za kuiandika. Mishale ya mviringo yenye namba moja na mbili inaelekeza kalamu kuzunguka duara na kurudi sehemu ya kuanzia.",
    "pg060_im011": "Mchoro unaonesha herufi kubwa O na herufi ndogo o za rangi ya kijivu hafifu juu ya usuli mweusi, zikiwa mfano wa kuandika herufi hizo pamoja.",
    "pg060_im012": "Mchoro unaonesha herufi kubwa O na herufi ndogo o za rangi ya kijivu hafifu juu ya usuli mweusi, zikiwa mfano wa pili wa kuandika herufi hizo pamoja.",
    "pg060_im013": "Mchoro unaonesha herufi kubwa O na herufi ndogo o za rangi ya kijivu hafifu juu ya usuli mweusi, zikiwa mfano wa tatu wa kuandika herufi hizo pamoja.",
    "pg060_im014": "Mchoro unaonesha herufi kubwa O na herufi ndogo o za rangi ya kijivu hafifu juu ya usuli mweusi, zikiwa mfano wa nne wa kuandika herufi hizo pamoja.",
    "pg060_im015": "Mchoro unaonesha herufi kubwa O na herufi ndogo o za rangi ya kijivu hafifu juu ya usuli mweusi, zikiwa mfano wa tano wa kuandika herufi hizo pamoja.",
    "pg065_im002": "Mchoro unaonesha herufi kubwa M nyeusi na mishale minne yenye namba moja hadi nne. Mishale inaelekeza mistari miwili ya wima na mistari miwili ya mshazari inayokutana katikati.",
    "pg069_im004_crop1": "Mchoro unaonesha herufi kubwa N nyeusi na mishale mitatu yenye namba. Hatua ya kwanza inashuka wima kushoto, ya pili inapanda kwa mshazari, na ya tatu inashuka wima kulia.",
    "pg071_im001": "Picha inaonesha mkoba wa shule wenye sehemu kubwa ya buluu, kingo za waridi, nyeusi na manjano, mfuko wa mbele wenye zipu na mikanda miwili ya kubebea mgongoni.",
    "pg071_im002": "Picha inaonesha maboga mawili makubwa ya rangi ya machungwa yaliyowekwa pamoja. Kila boga lina umbo la mviringo lililobonyea, mistari mingi ya wima na kikonyo kifupi cha kijani juu.",
    "pg071_im003": "Picha inaonesha dawati la shule la mbao la rangi ya kahawia, lenye sehemu ndefu ya kuandikia, benchi la kukalia na viunzi vya miguu vilivyounganishwa.",
    "pg071_im004": "Picha inaonesha kofia ya buluu yenye taji la mviringo, mishono inayoonekana na ukingo wa mbele wa rangi ya njano.",
    "pg071_im005": "Picha inaonesha nanasi moja lenye ganda la njano na kahawia lenye macho mengi, pamoja na taji la majani marefu ya kijani yenye ncha kali.",
    "pg075_im006_crop_v1": "Mchoro unaonesha herufi kubwa P yenye mshale wa hatua ya kwanza, ikifuatiwa na herufi P tano za nukta zilizopangwa kwenye mistari ya kuandikia ili kufuatishwa.",
    "pg077_im003_crop_v1_crop1": "Mchoro unaonesha herufi kubwa S nyeusi na mishale miwili ya mviringo. Hatua ya kwanza inapinda kutoka juu kuelekea katikati, na ya pili inaendelea kupinda hadi chini.",
    "pg082_im013_crop1": "Mchoro unaonesha herufi kubwa G nyeusi na mishale minne yenye namba. Mshale wa kwanza unazungusha umbo kubwa la C, kisha mistari ya pili, tatu na nne inaunda sehemu ya ndani ya G.",
    "pg097_im001": "Picha inaonesha sungura mweupe wa katuni akiruka na kutabasamu. Ana masikio marefu yenye rangi ya waridi ndani, fulana ya zambarau, suruali ya machungwa na mikono yote miwili iliyoinuliwa.",
    "pg100_im001": "Picha inaonesha shati la mikono mifupi lenye rangi ya zambarau hafifu, kola, vifungo vya waridi katikati, mfuko mmoja kifuani na mistari ya waridi kwenye mikono.",
    "pg100_im002": "Picha inaonesha shoka lenye kichwa cha chuma cha kijivu na makali mapana meupe, likiwa limefungwa kwenye mpini mrefu wa mbao wa rangi ya kahawia.",
    "pg104_im004_seg001_v1_crop1": "Picha inaonesha mbuni mwenye shingo na miguu mirefu ya rangi ya waridi-kahawia, mwili wenye manyoya meusi na meupe, kichwa kidogo na mdomo mfupi.",
    "pg104_im004_seg002_v1_crop1": "Picha inaonesha mbuzi wa rangi ya kahawia na nyeupe akisimama kwa miguu minne. Ana pembe mbili zilizopinda nyuma, masikio marefu, ndevu fupi na mkia ulioinuka.",
    "pg104_im004_seg003_v1_crop1": "Picha inaonesha wembe wa chuma wa rangi ya fedha, wenye umbo la mstatili, makali mawili marefu na matundu matatu katikati ya kukamatia.",
    "pg104_im004_seg004_v1_crop1": "Picha inaonesha lundo la mbao za rangi ya kahawia. Baadhi ni magogo yaliyokatwa na kupangwa nyuma, na nyingine ni mbao ndefu nyembamba zilizoegemezwa mbele.",
    "pg104_im004_seg005_v1_crop1": "Picha inaonesha simba dume wa rangi ya kahawia ya dhahabu, mwenye manyoya mengi meusi na kahawia shingoni. Amesimama kwa miguu minne na ana mkia mrefu wenye kishada cheusi.",
    "pg106_im001": "Picha inaonesha nyumba ndogo yenye kuta za rangi ya krimu, paa la kijani-buluu, mlango wa kahawia na madirisha matatu ya buluu, ikiwa imezungukwa na bustani fupi.",
    "pg106_im002": "Picha inaonesha nyani wa rangi ya kijivu-kahawia akitembea kwa miguu minne. Ana uso mweusi, mikono mirefu, sehemu nyekundu nyuma na mkia mrefu uliopinda juu.",
    "pg106_im003": "Picha inaonesha nyanya mbili nyekundu zilizoiva, zenye umbo la mviringo lenye mikunjo na vikonyo vya kijani vyenye ncha juu.",
    "pg106_im004": "Picha inaonesha nyati mkubwa wa rangi ya kahawia akisimama kwenye nyasi. Ana mwili mzito, miguu minne, masikio mapana na pembe mbili ndefu zilizopinda kuelekea juu.",
    "pg106_im005": "Picha inaonesha nyoka wa rangi ya kahawia akiwa amejikunja ardhini na kuinua kichwa. Shingo yake imepanuka kama kofia na sehemu ya chini ina rangi ya krimu.",
    "pg106_im006": "Picha inaonesha nyumbu wa rangi ya kahawia akisimama kwenye nyasi. Ana pembe mbili zilizopinda, ndevu chini ya shingo, manyoya meusi mgongoni na mkia mrefu.",
    "pg108_im001": "Picha inaonesha ngiri wa rangi ya kijivu-kahawia akiwa ameinamisha kichwa ardhini. Ana manyoya magumu mgongoni, miguu mifupi na meno mawili yaliyopinda karibu na mdomo.",
    "pg108_im002": "Picha inaonesha ngazi ndefu ya rangi ya kijivu na kahawia, yenye nguzo mbili za pembeni na vipandio tisa vya mlalo vilivyopangwa kwa nafasi sawa.",
    "pg108_im003": "Picha inaonesha ngamia wa rangi ya njano-kahawia akitembea kuelekea kulia. Ana miguu minne mirefu, shingo ndefu, kichwa kidogo na nundu moja mgongoni.",
    "pg108_im004": "Picha inaonesha ngoma ndefu ya rangi ya kahawia, yenye umbo la silinda linalopanuka juu, ngozi ya mviringo juu na kamba nyingi za wima kuzunguka mwili.",
    "pg108_im005": "Picha inaonesha kanga mwenye mwili wa buluu-kijivu uliojaa madoa meupe, kichwa kidogo chenye sehemu nyekundu na buluu, na miguu miwili myembamba.",
    "pg108_im006": "Picha inaonesha kengele ya chuma ya rangi ya dhahabu, yenye mdomo mpana, kishikio cha kahawia juu na kipigio kidogo cha mviringo ndani.",
    "pg110_im001": "Picha inaonesha ndala mbili za rangi ya waridi, zenye nyayo bapa na mikanda ya umbo la V inayopita juu ya vidole.",
    "pg110_im002": "Picha inaonesha ndege wa rangi ya kijani na buluu akiwa juu ya tawi. Ana kichwa cha machungwa, mdomo mwekundu, bawa la kijani na mkia mrefu wa kahawia.",
    "pg110_im003": "Picha inaonesha ndimu mbili za kijani; moja ni nzima na nyingine imekatwa katikati. Vipande vinaonesha maganda ya kijani na nyama ya ndani yenye sehemu nyingi za juisi.",
    "pg110_im004": "Picha inaonesha mkungu mdogo wa ndizi nne za njano zilizopinda, zikiwa zimeunganishwa kwenye kikonyo cha kahawia na zenye ncha nyeusi.",
    "pg110_im005": "Picha inaonesha ndoo ya plastiki ya buluu yenye umbo la silinda, mdomo mpana, sehemu ya ndani ya buluu hafifu na mpini mwembamba wa chuma.",
    "pg112_im001": "Picha inaonesha kwato la ng'ombe la rangi ya kahawia, likiwa na sehemu mbili ngumu zilizogawanyika mbele na manyoya mafupi meusi-kahawia juu ya mguu.",
    "pg115_im001": "Picha inaonesha familia ya watu watano wakila chakula mezani. Watu wazima wawili na watoto watatu wameketi kuzunguka meza yenye sufuria, sahani, vikombe na vyakula mbalimbali.",
    "pg115_im002": "Picha inaonesha familia ya watu wanne wameketi sebuleni wakitazama televisheni. Watu watatu wako kwenye kochi la kijani na mmoja kwenye kiti, huku televisheni ikiwa juu ya meza mbele yao.",
    "pg115_im003": "Picha inaonesha wasichana watatu wakicheza kuruka kamba nje. Wasichana wawili wameshika ncha za kamba, na msichana wa katikati aliyevaa gauni jekundu anaruka juu yake.",
}


def main() -> None:
    pages = [ROOT / "index.html", *sorted(ROOT.glob("pg???_sec001.html"))]
    found = set()
    for path in pages:
        source = path.read_text(encoding="utf-8")
        for image_id, description in DESCRIPTIONS.items():
            pattern = re.compile(rf'(<img\b(?=[^>]*\bdata-id="{re.escape(image_id)}")[^>]*\balt=")[^"]*(")')
            source, count = pattern.subn(lambda m, d=description: m.group(1) + html.escape(d, quote=True) + m.group(2), source)
            if count:
                found.add(image_id)
        if path.name == "pg071_sec001.html":
            pumpkin_pattern = re.compile(r'<img\b(?=[^>]*\bdata-id="pg071_im002")[^>]*>')
            pumpkins = list(pumpkin_pattern.finditer(source))
            if len(pumpkins) != 2:
                raise SystemExit(f"Expected two pumpkin drawings, found {len(pumpkins)}")
            duplicate = pumpkins[1]
            duplicate_tag = duplicate.group(0)
            duplicate_tag = re.sub(r'\sdata-id="pg071_im002"', "", duplicate_tag)
            duplicate_tag = re.sub(r'\salt="[^"]*"', ' alt=""', duplicate_tag)
            duplicate_tag = duplicate_tag[:-1] + ' aria-hidden="true" role="presentation">'
            source = source[:duplicate.start()] + duplicate_tag + source[duplicate.end():]
        path.write_text(source, encoding="utf-8")

    if found != set(DESCRIPTIONS):
        missing = sorted(set(DESCRIPTIONS) - found)
        raise SystemExit(f"Descriptions not linked from HTML: {', '.join(missing)}")

    for lang in ("sw", "sw-TZ"):
        path = ROOT / "content/i18n" / lang / "texts.json"
        texts = json.loads(path.read_text(encoding="utf-8"))
        texts.update(DESCRIPTIONS)
        path.write_text(json.dumps(texts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Applied {len(DESCRIPTIONS)} visually verified descriptions")


if __name__ == "__main__":
    main()
