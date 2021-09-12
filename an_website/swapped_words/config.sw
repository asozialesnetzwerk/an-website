# swapped words config
# rules:
# - must be separated by '=>' or '<=>'
# - lines that start with '#' are comments
# - white spaces outside of words are ignored
# - things that get replaced must be valid regex
# - words can't contain: '<', '=', '>'

am(ü|ue)sant         => relevant
relevant             => amüsant
am(ü|ue)sanz         => relevanz
relevanz             => amüsanz
ministerium         <=> mysterium
ministerien         <=> mysterien
sch(ü|ue)tzenverein  => bundestag
bundestag            => schützenverein
ironisch            <=> erotisch
ironien             <=> erotiken
ironie              <=> erotik
ironiker            <=> erotiker
problem             <=> ekzem
kritisch            <=> kryptisch
kritik              <=> kryptik
provozier           <=> produzier
arbeitnehmer        <=> arbeitgeber
arbeitsnehmer       <=> arbeitsgeber

# der Typ heißt Bernd!
# bj(ö|oe)rn h(ö|oe)cke => bernd höcke