"""Small hand-made landmark list used ONLY by the development mock resolver.

Coordinates are approximate (good to a block or so) and exist so the UI can be
built and demonstrated before the real OpenStreetMap / Photon pipeline (lane 1)
is ready. Do not treat this file as data.

Each entry: (id, name, name_ar, category, area, area_ar, lat, lng, aliases)
Aliases cover English, Arabic and common Arabizi spellings.
"""

LANDMARKS = [
    (
        "mar-elias-church", "Mar Elias Church", "كنيسة مار الياس", "church",
        "Mar Elias, Beirut", "مار الياس، بيروت", 33.8873, 35.4867,
        ["mar elias church", "mar elias", "saint elias church", "st elias church",
         "كنيسة مار الياس", "مار الياس", "kenise mar elias", "kniset mar elias", "mar elyas"],
    ),
    (
        "saint-charbel-jdeideh", "Saint Charbel Church", "كنيسة مار شربل", "church",
        "Jdeideh, Metn", "الجديدة، المتن", 33.8921, 35.5606,
        ["saint charbel church", "saint charbel", "st charbel", "mar charbel",
         "كنيسة مار شربل", "مار شربل", "القديس شربل", "kenise mar charbel", "mar sharbel"],
    ),
    (
        "aub-main-gate", "AUB Main Gate", "البوابة الرئيسية للجامعة الأميركية", "university",
        "Hamra, Beirut", "الحمرا، بيروت", 33.8993, 35.4797,
        ["aub main gate", "aub", "american university of beirut", "aub gate",
         "الجامعة الأميركية", "الجامعة الاميركية في بيروت", "بوابة الجامعة الأميركية",
         "el jem3a el amerkiye", "jem3it el amerkan", "bawabit aub"],
    ),
    (
        "bau-beirut", "Beirut Arab University", "جامعة بيروت العربية", "university",
        "Tariq El Jdideh, Beirut", "الطريق الجديدة، بيروت", 33.8735, 35.4962,
        ["beirut arab university", "bau", "arab university",
         "جامعة بيروت العربية", "الجامعة العربية",
         "jem3it bayrut el 3arabiye", "el jem3a el 3arabiye", "jem3a 3arabiye"],
    ),
    (
        "hamra-street", "Hamra Street", "شارع الحمرا", "street",
        "Hamra, Beirut", "الحمرا، بيروت", 33.8963, 35.4826,
        ["hamra street", "hamra st", "hamra", "شارع الحمرا", "الحمرا",
         "share3 el hamra", "chare3 el hamra", "el hamra"],
    ),
    (
        "sassine-square", "Sassine Square", "ساحة ساسين", "square",
        "Achrafieh, Beirut", "الأشرفية، بيروت", 33.8879, 35.5214,
        ["sassine square", "sassine", "ساحة ساسين", "ساسين", "sehet sassine", "se7it sassine"],
    ),
    (
        "abc-achrafieh", "ABC Achrafieh", "ABC الأشرفية", "mall",
        "Achrafieh, Beirut", "الأشرفية، بيروت", 33.8889, 35.5240,
        ["abc achrafieh", "abc mall", "abc", "abc الاشرفية", "el abc", "abc ashrafiye"],
    ),
    (
        "martyrs-square", "Martyrs' Square", "ساحة الشهداء", "square",
        "Downtown Beirut", "وسط بيروت", 33.8960, 35.5068,
        ["martyrs square", "ساحة الشهداء", "ساحة البرج", "sehet el shouhada", "se7it el borj"],
    ),
    (
        "al-amin-mosque", "Mohammad Al-Amin Mosque", "جامع محمد الأمين", "mosque",
        "Downtown Beirut", "وسط بيروت", 33.8951, 35.5060,
        ["mohammad al amin mosque", "al amin mosque", "blue mosque",
         "جامع محمد الأمين", "مسجد محمد الأمين", "جامع الأمين",
         "jeme3 mohammad el amin", "jemi3 el amin"],
    ),
    (
        "raouche-rock", "Raouche Rock", "صخرة الروشة", "landmark",
        "Raouche, Beirut", "الروشة، بيروت", 33.8899, 35.4712,
        ["raouche rock", "raouche", "pigeon rock", "صخرة الروشة", "الروشة",
         "sakhrit el raouche", "el raouche"],
    ),
    (
        "manara-lighthouse", "Manara Lighthouse", "منارة بيروت", "landmark",
        "Manara, Beirut", "المنارة، بيروت", 33.9003, 35.4717,
        ["manara lighthouse", "manara", "beirut lighthouse", "المنارة", "منارة بيروت", "el manara"],
    ),
    (
        "gouraud-street", "Gouraud Street, Gemmayzeh", "شارع غورو، الجميزة", "street",
        "Gemmayzeh, Beirut", "الجميزة، بيروت", 33.8960, 35.5168,
        ["gouraud street", "gemmayzeh", "gemmayze", "الجميزة", "شارع غورو", "el jemmayze"],
    ),
    (
        "armenia-street", "Armenia Street, Mar Mikhael", "شارع أرمينيا، مار مخايل", "street",
        "Mar Mikhael, Beirut", "مار مخايل، بيروت", 33.8982, 35.5240,
        ["armenia street", "mar mikhael", "مار مخايل", "شارع ارمينيا", "mar mkhayel"],
    ),
    (
        "verdun-street", "Rachid Karami Street, Verdun", "شارع رشيد كرامي، فردان", "street",
        "Verdun, Beirut", "فردان، بيروت", 33.8857, 35.4836,
        ["verdun street", "verdun", "rachid karami street", "فردان", "شارع فردان", "fardan"],
    ),
    (
        "cola-roundabout", "Cola Roundabout", "دوار الكولا", "roundabout",
        "Cola, Beirut", "الكولا، بيروت", 33.8800, 35.4945,
        ["cola roundabout", "cola bridge", "cola", "دوار الكولا", "جسر الكولا", "الكولا",
         "dawar el cola", "jesr el cola", "el cola"],
    ),
    (
        "sodeco-square", "Sodeco Square", "ساحة السوديكو", "square",
        "Achrafieh, Beirut", "الأشرفية، بيروت", 33.8892, 35.5108,
        ["sodeco square", "sodeco", "السوديكو", "el sodeco"],
    ),
    (
        "badaro-street", "Badaro Street", "شارع بدارو", "street",
        "Badaro, Beirut", "بدارو، بيروت", 33.8708, 35.5129,
        ["badaro street", "badaro", "شارع بدارو", "بدارو"],
    ),
    (
        "hotel-dieu", "Hôtel-Dieu de France Hospital", "مستشفى أوتيل ديو دو فرانس", "hospital",
        "Achrafieh, Beirut", "الأشرفية، بيروت", 33.8810, 35.5197,
        ["hotel dieu hospital", "hotel dieu", "hotel-dieu", "مستشفى اوتيل ديو", "اوتيل ديو",
         "mostashfa hotel dieu"],
    ),
    (
        "zaitunay-bay", "Zaitunay Bay", "زيتونة باي", "landmark",
        "Ain El Mreisseh, Beirut", "عين المريسة، بيروت", 33.9011, 35.4950,
        ["zaitunay bay", "zaitunay", "زيتونة باي", "الزيتونة", "zaytouna bay"],
    ),
    (
        "harissa-our-lady", "Our Lady of Lebanon, Harissa", "سيدة لبنان، حريصا", "church",
        "Harissa, Keserwan", "حريصا، كسروان", 33.9818, 35.6515,
        ["our lady of lebanon", "harissa", "سيدة لبنان", "حريصا", "سيدة حريصا",
         "saydet harissa", "saydit lebnen"],
    ),
    (
        "byblos-citadel", "Byblos Citadel", "قلعة جبيل", "landmark",
        "Byblos", "جبيل", 34.1196, 35.6458,
        ["byblos citadel", "byblos", "jbeil", "قلعة جبيل", "جبيل", "2al3it jbeil"],
    ),
]
