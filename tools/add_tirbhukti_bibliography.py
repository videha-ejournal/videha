from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERN = "videha-mithila-tirbhukti-tirhut-continuation-"

BIBLIOGRAPHY = """<section class=\"references\"><h2>सन्दर्भ-सूची / Bibliography</h2>
<p class=\"bibliography-note\"><strong>सम्पादकीय स्रोत-टिप्पणी:</strong> मूल 2008 ई. पाठमे औपचारिक bibliography नहि देल गेल छल। निम्न सूचीमे लेखसभमे प्रत्यक्ष रूपेँ उल्लिखित वा स्पष्ट रूपेँ पहिचानल जा सकनिहार प्राथमिक/द्वितीयक स्रोत सभकेँ एकत्र कएल गेल अछि। जतय मूल पाठ संस्करण, प्रकाशक वा पृष्ठ नहि देलक, ओहि ठाम विवरणकेँ अनुमानसँ नहि भरल गेल अछि।</p>
<ol>
<li><cite>Ṛgveda</cite>, 1.53.7 (Nami Sapya आ Videha-सन्दर्भ); Jamison, Stephanie W., and Joel P. Brereton, trans. <cite>The Rigveda: The Earliest Religious Poetry of India</cite>. Oxford University Press, 2014.</li>
<li><cite>Śatapatha Brāhmaṇa</cite>, विशेषतः Videgha Māthava, Sadanīrā आ Janaka प्रसंग; Eggeling, Julius, trans. <cite>The Satapatha Brahmana</cite>. Sacred Books of the East, vols. 12, 26, 41, 43, 44. Oxford: Clarendon Press, 1882–1900.</li>
<li><cite>Bṛhadāraṇyaka Upaniṣad</cite>, Janaka–Yājñavalkya संवाद; Olivelle, Patrick, trans. <cite>The Early Upaniṣads</cite>. Oxford University Press, 1998.</li>
<li><cite>Taittirīya Saṃhitā</cite>, Vaideha cows-सन्दर्भ; Keith, Arthur Berriedale, trans. <cite>The Veda of the Black Yajus School</cite>. Harvard Oriental Series, 18–19, 1914.</li>
<li>Vālmīki. <cite>Vālmīki Rāmāyaṇa</cite>, critical edition. Oriental Institute, Baroda, 1960–1975.</li>
<li>Vyāsa. <cite>Mahābhārata</cite>, critical edition. Bhandarkar Oriental Research Institute, Pune, 1933–1966.</li>
<li><cite>Viṣṇu Purāṇa</cite>. Wilson, H. H., trans. <cite>The Vishnu Purana</cite>. 1840; later revised editions.</li>
<li><cite>Bhāgavata Purāṇa</cite>, Videha/Nimi–Mithi genealogy passages. Edition not specified in the original article.</li>
<li><cite>Garuḍa Purāṇa</cite>, Videha genealogy passages. Edition not specified in the original article.</li>
<li><cite>Brahmavaivarta Purāṇa</cite>, Vedavatī/Kusadhvaja narrative. Edition not specified in the original article.</li>
<li><cite>Dīgha Nikāya</cite> and related Pāli canonical passages on Videha, Vajji and Mithilā. Pāli Text Society editions/translations.</li>
<li><cite>Jātaka</cite> corpus, Mithilā/Videha narratives. Cowell, E. B., ed. <cite>The Jātaka</cite>. Cambridge University Press, 1895–1907.</li>
<li><cite>Lalitavistara</cite>, script and Videha-related passages. Vaidya, P. L., ed. <cite>Lalitavistara</cite>. Buddhist Sanskrit Texts, 1958.</li>
<li>Xuanzang (Hiuen Tsang). <cite>Si-Yu-Ki: Buddhist Records of the Western World</cite>. Beal, Samuel, trans. Trübner, 1888.</li>
<li>Basarh seals, Panchobh copper-plate and related epigraphic evidence cited in the series; consult <cite>Epigraphia Indica</cite> and the <cite>Archaeological Survey of India Annual Reports</cite> for the individual inscription records.</li>
<li>Choudhary, Radhakrishna. <cite>History of Bihar</cite>. Motilal Banarsidass, 1958.</li>
<li>Choudhary, Radhakrishna. <cite>Mithilā in the Age of Vidyāpati</cite>. Chaukhambha Orientalia, 1976.</li>
<li>Thakur, Upendra. <cite>History of Mithila</cite>. 1956. Full publication details are not supplied in the source text.</li>
<li>Sarkar, S. C. Studies on the Janaka/Vedavatī traditions, as cited in continuation 1. The original text does not provide a complete title or publication record.</li>
<li>Thakur, Gajendra. “Videha, Mithila, Tirbhukti, Tirhut,” continuations 1–3 and 5–8. <cite>Videha — First Maithili Fortnightly eJournal</cite>, issues 2, 3, 9, 11–14, 2008. ISSN 2229-547X.</li>
</ol></section>"""

ADDITIONAL = """<li>Mishra, Yogendra. <cite>History of Videha: From the Earliest Times to the Foundation of the Gupta Empire, A.D. 319</cite>. Patna: Janaki Prakashan, 1981.</li>
<li>Sinha, Chandreshwar Prasad Narayan (C. P. N. Sinha). <cite>Mithila Under the Karnatas, c. 1097–1325 A.D.</cite> Patna: Janaki Prakashan, 1979.</li>"""

changed = []
for path in sorted((ROOT / "research").rglob("*.htm")):
    if PATTERN not in path.stem:
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    if "सन्दर्भ-सूची / Bibliography" in text:
        if "History of Videha: From the Earliest Times" not in text:
            marker_existing = '<li>Choudhary, Radhakrishna.'
            text = text.replace(marker_existing, ADDITIONAL + marker_existing, 1)
            path.write_text(text, encoding="utf-8")
            changed.append(path.relative_to(ROOT).as_posix() + " (supplemented)")
        continue
    marker = '<section class="citation">'
    if marker not in text:
        print(f"SKIP (citation marker missing): {path}")
        continue
    text = text.replace(marker, BIBLIOGRAPHY + marker, 1)
    path.write_text(text, encoding="utf-8")
    changed.append(path.relative_to(ROOT).as_posix())

print(f"Added bibliography to {len(changed)} pages")
for item in changed:
    print(item)
