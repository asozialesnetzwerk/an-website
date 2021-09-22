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
Relevanz             => Amüsanz
Ministerium         <=> Mysterium
Ministerien         <=> Mysterien
Sch(ü|ue)tzenverein  => Bundestag
Bundestag            => Schützenverein
ironisch            <=> erotisch
Ironien             <=> Erotiken
Ironie              <=> Erotik
Ironiker            <=> Erotiker
Problem             <=> Ekzem
kritisch            <=> kryptisch
Kritik              <=> Kryptik
provozier           <=> produzier
Arbeitnehmer        <=> Arbeitgeber
Arbeitsnehmer       <=> Arbeitsgeber

# der Typ heißt Bernd!
# Bj(ö|oe)rn H(ö|oe)cke => Bernd Höcke
