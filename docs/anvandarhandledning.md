# Höjdkurvsetiketter: användarhandledning

Pluginet *Contour Labeler* (visas som **Höjdkurvsetiketter** när QGIS körs på svenska) placerar höjdsiffror på höjdkurvor så som en kartograf gör det: du ritar en **etikettstege**, en guidelinje uppför över kurvorna, och en etikett läggs där linjen korsar varje kurva. Texten följer kurvans riktning och texttoppen pekar uppför.

Handledningen gäller version 0.1.1 och QGIS 3.34 eller senare (inklusive QGIS 4).

## Det här behöver du

- Ett **linjelager med höjdkurvor** där varje kurva har ett numeriskt höjdvärde i ett fält (till exempel `elev`, `z` eller `height`).
- Inget annat. Du behöver inget separat guidelager.

## Öppna panelen

Klicka på pluginets ikon i verktygsfältet eller välj **Plugins ▸ Höjdkurvsetiketter**. Panelen dockas till höger om kartan. Klicka på ikonen igen för att dölja den.

## Arbetsgång

1. **Välj höjdkurvlager.** Rullgardinen visar alla linjelager i projektet.
2. **Kontrollera höjdfältet.** Pluginet gissar fältet (`elev`, `ele`, `z`, `height`, `hojd`, `höjd`, `altitude`, `value`). Är det fel väljer du rätt fält själv. Bara numeriska fält visas.
3. **Välj typsnitt** med knappen *Typsnitt för etiketter* (se nedan).
4. Klicka på **Rita etikettstege**. Knappen blir intryckt och markören ändras till ett hårkors.
5. **Rita guidelinjen uppför:** vänsterklicka där linjen ska börja, klicka vidare över kurvorna och avsluta med **högerklick** eller **Enter**. En röd linje visar vad du ritar.
6. Etiketterna läggs ut direkt. Statusraden under knapparna säger hur många som lades till.
7. Rita nästa guidelinje direkt. Verktyget är kvar tills du klickar på knappen igen eller väljer ett annat verktyg i QGIS.

### Tangenter när du ritar

| Tangent | Gör |
|---|---|
| Vänsterklick | Lägger till en punkt |
| Högerklick eller Enter | Avslutar guidelinjen och lägger ut etiketterna |
| Backsteg | Tar bort den senaste punkten |
| Esc | Avbryter pågående guidelinje |
| Ctrl+Z | Ångrar senaste stegen (kartfönstret måste ha fokus) |

## Så avgörs etikettens riktning

- **Texttoppen pekar åt det håll du ritade guidelinjen.** Rita därför alltid uppför. Ritar du nedför blir texten upp och ner.
- Grundlinjen följer kurvans riktning vid korsningen. Det spelar ingen roll i vilken riktning kurvan en gång digitaliserades.
- Är guidelinjen böjd används riktningen hos det segment som korsar kurvan, så du kan följa en brant sluttning med flera punkter.
- Kurvor utan höjdvärde hoppas över.

## Ångra

Resultatet beror på hur du drar guidelinjen, så missnöjda ritar bara om:

- **Ångra senaste stegen** tar bort alla etiketter från den senaste guidelinjen. Du kan ångra flera steg bakåt, ett per guidelinje.
- Ångra-listan nollställs när QGIS startas om eller pluginet laddas om. Då ligger etiketterna kvar i lagret och får tas bort för hand.

## Typsnitt och halo

Knappen *Typsnitt för etiketter* öppnar QGIS vanliga textformatpanel: typsnitt, storlek, färg, **buffert** och mer. Ändringar slår igenom direkt på utlagret, och valet minns mellan sessioner.

Som standard har texten en **vit halo** (buffert, 1,2 mm) som döljer höjdkurvan bakom siffran. Har kartan en annan bakgrundsfärg ställer du in halons färg under **Buffer**, gärna med pipetten så att du tar färgen direkt från kartan. Du kan också stänga av bufferten eller göra den smalare.

## Utlagret

Etiketterna hamnar i ett punktlager som heter **Höjdkurvsetiketter**:

| Fält | Innehåll |
|---|---|
| `elev` | Höjdvärdet från kurvan |
| `rotation` | Etikettens rotation (grader medurs) |

- Lagret är **tillfälligt** (ett minneslager). Det försvinner när projektet stängs om du inte sparar det.
- Klicka på **Spara resultat…** när du är nöjd. QGIS exportdialog öppnas, där du väljer format (till exempel GeoPackage) och filnamn.
- Efter exporten arbetar pluginet fortfarande mot det tillfälliga lagret. Ritar du fler stegar behöver du exportera igen, så avsluta helst alla stegar först.
- Lagret har samma koordinatsystem som höjdkurvlagret. Guidelinjen ritas i kartans koordinatsystem och räknas om automatiskt.
- Etiketterna är vanliga punkter. Du kan flytta dem och ändra `rotation` med QGIS redigeringsverktyg.
- Etiketterna ändras inte om du ändrar höjdkurvorna efteråt. Ta då bort dem och rita om.

## Inställningar

Under **Inställningar** finns **Utjämningsavstånd** (standard 5 m): hur långt åt varje håll från korsningen som kurvans riktning mäts. Ökar du värdet blir etiketterna lugnare på ojämna kurvor. Minska det för kurvor med skarpa svängar.

## Tips

- **Bara vissa kurvor ska ha etiketter** (till exempel var 25:e meter): filtrera höjdkurvlagret först (högerklicka på lagret, *Filtrera…*, till exempel `"elev" % 25 = 0`). Pluginet märker alla kurvor guidelinjen korsar i lagret som visas av filtret.
- **Håll guidelinjen rak och ungefär vinkelrät mot kurvorna.** Då blir etiketterna prydligt staplade som stegpinnar.
- **Etiketter tätt intill varandra:** rita guidelinjen på en plats där kurvorna ligger glesare, eller lägg guidelinjer med jämna mellanrum längs sluttningen.
- Korsar guidelinjen kurvan exakt i en av dina punkter får du ändå bara en etikett.

## Felsökning

| Du ser | Orsak och åtgärd |
|---|---|
| *Rita etikettstege* är grå | Välj först ett höjdkurvlager och ett höjdfält. |
| "Inga etiketter: guidelinjen korsade ingen höjdkurva med höjdvärde." | Guidelinjen nådde inte någon kurva, eller kurvorna saknar värde i det valda fältet. Kontrollera fältet. |
| Texten står upp och ner | Guidelinjen ritades nedför. Ångra och rita uppför. |
| Siffrorna syns inte | Kontrollera att lagret *Höjdkurvsetiketter* är synligt och ligger ovanför höjdkurvorna i lagerpanelen. |
| Panelen syns inte | Klicka på ikonen igen. Den kan ha gömts bakom en annan flikad panel. |
| Etiketter försvann efter omstart | Utlagret var tillfälligt och sparades inte. Använd *Spara resultat…*. |

## Mer information

- Källkod, felrapporter och engelsk beskrivning: https://github.com/matself/contour-labeler
- Pluginet är licensierat under GPL-2.0-or-later.
