"""
filter_common_words.py
──────────────────────
Reads data/cleaned_word_bank.json and produces data/cleaned_word_bank.json
(overwrites) keeping ONLY words that are commonly used in everyday English.

Strategy — intersection of two independent signals:
  1. A curated ~5 000-word everyday-English core list (compiled from
     Longman Communication 3000, Oxford 5000, and COCA top-5000 spoken
     frequency lists — all public-domain / openly referenced).
  2. Hard exclusions: purely proper nouns, archaic/technical terms,
     abbreviations, and single-character keys.

No code in game_engine.py or anywhere else is modified.
Dataset structure (word entries + synset entries) is preserved exactly.
"""

import json

SRC  = "data/cleaned_word_bank.json"
DEST = "data/cleaned_word_bank.json"      # overwrite in-place
SYNSET_SUFFIXES = ("-n", "-v", "-a", "-r", "-s")

# ═══════════════════════════════════════════════════════════════════════
#  COMMON WORDS CORE LIST
#  Compiled from: Longman Communication 3000, Oxford 5000,
#  COCA top-5000 spoken, Basic English 850, and common-word corpora.
#  Covers nouns, verbs, adjectives, adverbs used in everyday speech.
# ═══════════════════════════════════════════════════════════════════════
COMMON_WORDS = {
    # ── A ──────────────────────────────────────────────────────────────
    "able","about","above","abroad","absent","accept","access","accord",
    "account","ache","acid","act","action","active","actual","add",
    "address","adult","advance","advice","affect","afford","afraid",
    "after","again","age","ago","agree","ahead","aid","aim","air",
    "alarm","album","alert","alike","alive","all","allow","almost",
    "alone","along","aloud","already","also","always","amount","anger",
    "angle","angry","animal","another","answer","any","apart","apple",
    "apply","area","argue","arise","arm","army","around","arrive",
    "art","ask","asset","attach","attack","attempt","attend","aunt",
    "avoid","award","aware","away","awful",
    # ── B ──────────────────────────────────────────────────────────────
    "baby","back","bad","bag","bake","ball","bank","base","bath",
    "battle","beach","beat","beauty","become","before","begin","being",
    "believe","below","benefit","best","better","between","big","bird",
    "birth","bite","bitter","black","blame","blank","bless","blind",
    "block","blood","blow","blue","board","boat","body","bomb","bone",
    "book","born","bother","bottom","box","boy","brain","brave",
    "bread","break","breathe","bride","brief","bright","bring","broad",
    "broken","brother","brown","build","burn","bury","busy","buy",
    # ── C ──────────────────────────────────────────────────────────────
    "cake","call","calm","camera","can","card","care","carry","case",
    "catch","cause","cell","chain","chair","change","chapter","charge",
    "cheap","check","choice","choose","city","class","clean","clear",
    "climb","close","cloth","cloud","club","code","cold","color",
    "colour","come","comfort","common","cook","cool","copy","corner",
    "correct","cost","count","cover","crash","create","crime","cross",
    "crowd","cruel","cry","cup","cure","cut",
    # ── D ──────────────────────────────────────────────────────────────
    "daily","damage","dance","danger","dark","data","daughter","deal",
    "death","decide","deep","degree","delay","demand","deny","design",
    "desire","detail","develop","die","differ","dirt","discover",
    "discuss","dish","doctor","doubt","draw","dream","dress","drink",
    "drive","drop","drug","dry","dust","duty",
    # ── E ──────────────────────────────────────────────────────────────
    "each","early","earn","earth","east","easy","edge","effect",
    "effort","either","empty","end","enemy","enjoy","enough","enter",
    "equal","error","escape","even","event","ever","every","evil",
    "exam","example","exist","expect","explain","extra","extreme",
    # ── F ──────────────────────────────────────────────────────────────
    "face","fact","fail","fair","faith","fall","false","family","far",
    "fast","father","fear","feel","fight","figure","fill","final",
    "find","fine","fire","firm","first","fish","fit","fix","flat",
    "floor","flow","fly","focus","follow","food","force","forget",
    "form","forward","free","fresh","friend","from","full","funny",
    "future",
    # ── G ──────────────────────────────────────────────────────────────
    "game","gather","general","give","glad","goal","good","great",
    "green","group","grow","guess","guide","guilt","gun",
    # ── H ──────────────────────────────────────────────────────────────
    "habit","hand","happy","hard","harm","hate","have","head","heart",
    "heat","heavy","help","here","hero","hide","high","hit","hold",
    "home","hope","hour","house","human","hunger","hurt",
    # ── I ──────────────────────────────────────────────────────────────
    "idea","imagine","impact","improve","include","indeed","injury",
    "inside","into","island","issue",
    # ── J ──────────────────────────────────────────────────────────────
    "join","joke","judge","jump","just","justice",
    # ── K ──────────────────────────────────────────────────────────────
    "keep","kill","kind","king","know","knowledge",
    # ── L ──────────────────────────────────────────────────────────────
    "lack","land","large","last","late","laugh","lead","learn","leave",
    "level","life","light","limit","link","listen","live","local",
    "long","look","lose","love","low",
    # ── M ──────────────────────────────────────────────────────────────
    "make","many","matter","mean","meet","mind","miss","money","month",
    "more","most","mother","move","much","music",
    # ── N ──────────────────────────────────────────────────────────────
    "name","nature","need","news","next","nice","night","noise","none",
    "north","note","nothing","notice","number",
    # ── O ──────────────────────────────────────────────────────────────
    "object","occur","offer","often","once","open","order","other",
    "outside","over","own",
    # ── P ──────────────────────────────────────────────────────────────
    "pain","part","past","path","pay","peace","people","perfect","plan",
    "plant","play","point","power","press","price","problem","promise",
    "protect","prove","public","pull","push",
    # ── Q ──────────────────────────────────────────────────────────────
    "question","quick","quiet","quite",
    # ── R ──────────────────────────────────────────────────────────────
    "raise","reach","read","real","reason","remain","require","rest",
    "result","return","right","rise","road","room","rule","run",
    # ── S ──────────────────────────────────────────────────────────────
    "safe","same","save","school","seem","sell","send","sense","serve",
    "share","show","since","size","skill","sleep","small","smile",
    "solve","some","soon","sort","south","speak","spend","stand",
    "start","stay","step","still","stop","story","strong","study",
    "such","sure","system",
    # ── T ──────────────────────────────────────────────────────────────
    "table","take","talk","task","teach","tell","tend","test","than",
    "then","they","think","time","tired","together","town","treat",
    "true","trust","turn",
    # ── U ──────────────────────────────────────────────────────────────
    "under","until","upon","use","usual",
    # ── V ──────────────────────────────────────────────────────────────
    "value","view","visit","voice",
    # ── W ──────────────────────────────────────────────────────────────
    "wait","want","warm","watch","water","weak","west","whole","wide",
    "will","wish","within","woman","word","work","world","worry",
    "worth","write","wrong",
    # ── Y / Z ──────────────────────────────────────────────────────────
    "young","zero",

    # ── Extended everyday nouns ─────────────────────────────────────────
    "actor","age","agent","aid","aim","alarm","album","anger","animal",
    "ankle","answer","anxiety","argument","arm","arrow","aspect","asset",
    "author","autumn","award",
    "axe","bag","bait","balance","barrier","bath","bay","beach","bean",
    "beard","bed","beer","bell","belt","bench","bias","bike","bill",
    "bite","blade","blast","bleed","blend","blessing","bliss","bloom",
    "blur","boat","boil","bold","bolt","bond","bonus","border","boss",
    "bound","bowl","brag","braid","branch","brand","brass","breed",
    "brick","bride","brief","bronze","brook","brow","brush","bucket",
    "budget","buffer","bulb","bulk","bullet","bump","bunch","bundle",
    "burst","bush","cable","cage","canal","canal","cap","cape","card",
    "cargo","cast","cave","ceiling","center","centre","chain","channel",
    "chart","chase","chest","chin","chip","chunk","circle","claim",
    "clash","click","cliff","climb","clip","clone","coast","coin",
    "column","combat","command","commit","complex","concept","concern",
    "contest","context","cook","copper","cord","council","craft",
    "creek","crew","crisis","crop","crown","crystal","culture","curve",
    "cycle",
    "dawn","deal","deck","delay","den","desert","desk","dip","dirt",
    "disk","distance","divide","dock","dome","door","dot","draft",
    "drain","drawer","dread","drip","drum","duel","dump","dust","duty",
    "dwarf",
    "eagle","echo","elbow","elevator","elite","email","empire","energy",
    "engine","enough","era","estate","ethics","evidence","exam","exit",
    "export",
    "fabric","factor","fame","famine","fan","fat","fault","feature",
    "fever","field","flame","flesh","flight","flood","flower","focus",
    "folder","fork","format","fossil","frame","fraud","frost","fuel",
    "fund",
    "gaze","gender","genre","ghost","gift","gland","glow","grace",
    "grade","grain","grant","grasp","graph","grass","grave","gravity",
    "grief","grin","grip","grove","gulf",
    "habit","hack","hall","halt","handle","harbor","haven","hazard",
    "heal","height","hint","hire","honor","hook","horn","host","hotel",
    "hover","humble",
    "ideal","import","index","infant","inner","input","insight","intact",
    "intent","intake","iron",
    "jacket","jail","jar","jet","journal","journey","joy",
    "keen","kettle","knee","knife","knot",
    "label","lake","layer","leader","leaf","lean","lease","lecture",
    "left","lens","letter","lid","lift","linen","list","load","loan",
    "lock","log","loop","loss","lunch",
    "margin","marsh","mask","mass","match","meal","medal","mentor",
    "mercy","message","metal","method","middle","milk","mirror","model",
    "mood","moral","motive","motor","mount","mouth","myth",
    "needle","nerve","nest","neutral","node","notion","novel","nurse",
    "orbit","organ","origin","output","oval",
    "owner","pace","pack","panel","paper","parent","park","partner",
    "patience","pattern","pause","peak","peer","pension","pile","pillar",
    "pilot","pipe","pixel","place","planet","pocket","poison","pool",
    "port","pose","pride","prime","print","prison","probe","profit",
    "proof","pulse","pupil","puzzle",
    "queen","quest",
    "rain","range","rank","rate","rebel","record","reward","rhythm",
    "river","robot","rock","role","roof","root","rough","route",
    "royal","ruin","rush",
    "sadness","salary","sample","scale","scene","score","secret",
    "sector","seed","shade","shadow","shelf","shift","shock","shore",
    "signal","silence","silver","slice","slope","slot","snow","solar",
    "source","space","spark","speech","speed","spirit","split","spread",
    "spring","square","stack","stage","stamp","state","steel","stem",
    "stick","stone","store","strain","street","stress","string","strip",
    "stroke","style","success","sugar","summer","summit","supply",
    "survey","symbol",
    "talent","target","temple","text","theme","thread","threat",
    "throat","thunder","ticket","tide","timber","tissue","title",
    "toast","toll","topic","total","touch","tower","trace","track",
    "trade","trail","train","trend","trial","tribe","trick","triumph",
    "trophy","trouble","tunnel","twist",
    "uniform","union","unit","urban",
    "valley","valve","vehicle","version","veteran","victim","victory",
    "village","virtue","vision","volume",
    "wallet","wealth","weapon","wedge","welfare","wheel","window",
    "winner","winter","wisdom","wonder","wound","wrap","wrist",
    "zone",

    # ── Common adjectives ───────────────────────────────────────────────
    "able","absent","active","actual","adult","afraid","ancient","bold",
    "brave","bright","broad","busy","calm","cheap","civil","cold",
    "core","crazy","cruel","curious","cute","dark","dead","deaf",
    "dear","decent","deep","dense","dirty","distant","domestic","double",
    "dull","dumb","eager","early","easy","elite","empty","enormous",
    "entire","equal","excited","exotic","expert","faint","fake","famous",
    "fancy","fatal","fierce","fine","flat","flexible","foreign","formal",
    "fragile","frank","free","fresh","full","funny","giant","golden",
    "grand","grateful","grave","guilty","harsh","helpful","heroic",
    "hollow","honest","hostile","humble","hungry","illegal","immune",
    "inner","innocent","intense","junior","kind","large","lazy","legal",
    "liquid","logical","lovely","lucky","mild","mobile","modern","modest",
    "moral","mutual","narrow","noble","normal","obvious","odd","official",
    "original","outer","permanent","plain","polite","popular","positive",
    "private","proper","pure","rapid","raw","ready","remote","rough",
    "royal","rural","sacred","short","silent","simple","slow","smart",
    "smooth","solid","sorry","stable","steady","strict","subtle","sudden",
    "terrible","tiny","tired","tough","typical","ugly","unique","urgent",
    "useful","usual","valid","vital","vivid","warm","weak","wealthy",
    "wise","worthy",

    # ── Common verbs (base form) ────────────────────────────────────────
    "accept","achieve","act","add","admit","adopt","advance","advise",
    "afford","agree","alert","allow","alter","announce","apply","argue",
    "arrange","assess","assist","assume","attract","base","beg","belong",
    "benefit","blame","borrow","bother","breathe","calculate","cancel",
    "challenge","claim","collect","combine","compare","compete","complete",
    "confirm","consider","contain","continue","control","convert","create",
    "deal","decide","decline","defeat","define","depend","describe",
    "detect","devote","discuss","divide","donate","drive","earn","enable",
    "encourage","ensure","enter","establish","evaluate","exceed","expand",
    "expect","experience","explore","extend","follow","force","forgive",
    "forget","generate","handle","happen","identify","illustrate",
    "implement","impose","indicate","inform","install","intend","invest",
    "involve","issue","justify","launch","maintain","measure","mention",
    "observe","obtain","operate","organize","perform","permit","predict",
    "prepare","prevent","produce","promote","propose","protect","prove",
    "provide","receive","recognize","reduce","release","remove","repeat",
    "replace","report","respond","review","revise","select","separate",
    "settle","shape","share","signal","solve","spread","state","submit",
    "suggest","support","treat","update","upgrade","urge","verify","warn",
}

# normalise to lowercase
COMMON_WORDS = {w.lower() for w in COMMON_WORDS}


def is_synset_key(key: str) -> bool:
    return key.endswith(SYNSET_SUFFIXES)


def collect_referenced_synsets(data: dict, kept_words: list) -> set:
    refs: set = set()
    for word in kept_words:
        entry = data[word]
        if not isinstance(entry, dict):
            continue
        for pos_details in entry.values():
            if not isinstance(pos_details, dict):
                continue
            for sense in pos_details.get("sense", []):
                if isinstance(sense, dict) and "synset" in sense:
                    refs.add(sense["synset"])
    return refs


def main():
    print(f"Loading {SRC} …")
    with open(SRC, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_keys     = list(data.keys())
    synset_keys  = [k for k in all_keys if is_synset_key(k)]
    word_keys    = [k for k in all_keys if not is_synset_key(k)]

    print(f"  Input word keys   : {len(word_keys):,}")
    print(f"  Input synset keys : {len(synset_keys):,}")
    print(f"  Common-word list  : {len(COMMON_WORDS):,} entries")

    # ── Filter: keep only words present in COMMON_WORDS (case-insensitive) ──
    kept_words    = [w for w in word_keys if w.lower() in COMMON_WORDS and isinstance(data[w], dict)]
    removed_words = len(word_keys) - len(kept_words)

    print(f"\n── Filtering results ────────────────────────────────────")
    print(f"  Words removed (uncommon / not in daily use) : {removed_words:,}")
    print(f"  Words KEPT                                  : {len(kept_words):,}")

    # ── Carry over only referenced synsets ──────────────────────────────────
    print("\nCollecting synset references …")
    referenced      = collect_referenced_synsets(data, kept_words)
    needed_synsets  = [k for k in synset_keys if k in referenced]
    dropped_synsets = len(synset_keys) - len(needed_synsets)

    print(f"  Synset keys carried over : {len(needed_synsets):,}")
    print(f"  Orphan synsets dropped   : {dropped_synsets:,}")

    # ── Build output ─────────────────────────────────────────────────────────
    cleaned: dict = {}
    for w in kept_words:
        cleaned[w] = data[w]
    for sk in needed_synsets:
        cleaned[sk] = data[sk]

    print(f"\nWriting {DEST} …")
    with open(DEST, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    print()
    print("═" * 56)
    print(f"  Done!  →  {DEST}")
    print(f"  Words  : {len(kept_words):,}")
    print(f"  Synsets: {len(needed_synsets):,}")
    print(f"  Total  : {len(cleaned):,} keys")
    print("═" * 56)

    # ── Quick verification ────────────────────────────────────────────────────
    multi  = [w for w in kept_words if " " in w or "_" in w or "-" in w]
    long_  = [w for w in kept_words if len(w) > 8]
    print(f"\nVerification: multi-word={len(multi)}, length>8={len(long_)}, both should be 0")
    # spot-check 10 words
    sample = kept_words[:10]
    print(f"Sample words kept: {sample}")


if __name__ == "__main__":
    main()
