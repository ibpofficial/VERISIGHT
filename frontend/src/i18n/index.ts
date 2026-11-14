export type Language = 'en' | 'hi';

export interface Translations {
  [key: string]: {
    en: string;
    hi: string;
  };
}

export const translations: Translations = {
  // Navigation & General
  'nav.command_center': {
    en: 'Command Center',
    hi: 'कमांड सेंटर (Command Center)',
  },
  'nav.new_screening': {
    en: 'New Screening',
    hi: 'नई जांच (New Screening)',
  },
  'nav.quick_check': {
    en: 'Quick Check',
    hi: 'त्वरित जांच (Quick Check)',
  },
  'nav.cases': {
    en: 'Investigation Cases',
    hi: 'जांच मामले (Investigation Cases)',
  },
  'nav.audit': {
    en: 'Audit Trail',
    hi: 'ऑडिट ट्रेल (Audit Trail)',
  },
  'nav.help': {
    en: 'Help Center',
    hi: 'सहायता केंद्र (Help Center)',
  },
  'nav.engine_status': {
    en: 'Engine Status',
    hi: 'इंजन स्थिति (Engine Status)',
  },
  'nav.user_mgmt': {
    en: 'User Management',
    hi: 'उपयोगकर्ता प्रबंधन (User Management)',
  },
  'nav.system_config': {
    en: 'System Config',
    hi: 'सिस्टम कॉन्फ़िगरेशन (System Config)',
  },

  // Mode & Language
  'mode.simple': {
    en: 'Simple Mode',
    hi: 'सरल मोड (Simple Mode)',
  },
  'mode.expert': {
    en: 'Expert Mode',
    hi: 'विशेषज्ञ मोड (Expert Mode)',
  },
  'mode.toggle_tooltip': {
    en: 'Switch between plain-language summaries and in-depth technical telemetry',
    hi: 'सरल भाषा सारांश और गहन तकनीकी डेटा के बीच टॉगल करें',
  },

  // Mandatory Decision-Support Disclaimer
  'disclaimer.decision_support': {
    en: 'This is an automated decision-support screening aid. A trained security officer always makes the final determination.',
    hi: 'यह एक स्वचालित निर्णय-सहायक स्क्रीनिंग उपकरण है। अंतिम निर्णय हमेशा एक प्रशिक्षित सुरक्षा अधिकारी द्वारा लिया जाता है।',
  },

  // Case Stepper Steps
  'step.1': {
    en: '1. Create Case',
    hi: '1. मामला बनाएं (Create Case)',
  },
  'step.1.desc': {
    en: 'Initiate screening reference and officer assignment',
    hi: 'स्क्रीनिंग संदर्भ और अधिकारी असाइनमेंट शुरू करें',
  },
  'step.2': {
    en: '2. Add Documents',
    hi: '2. दस्तावेज़ जोड़ें (Add Documents)',
  },
  'step.2.desc': {
    en: 'Upload primary and supporting travel credentials',
    hi: 'प्राथमिक और सहायक यात्रा दस्तावेज़ अपलोड करें',
  },
  'step.3': {
    en: '3. Automated Checks',
    hi: '3. स्वचालित जांच (Automated Checks)',
  },
  'step.3.desc': {
    en: 'Quality inspection, OCR, and passport security code math',
    hi: 'गुणवत्ता जांच, ओसीआर (OCR), और पासपोर्ट सुरक्षा कोड गणना',
  },
  'step.4': {
    en: '4. Review Findings',
    hi: '4. निष्कर्ष समीक्षा (Review Findings)',
  },
  'step.4.desc': {
    en: 'Examine tamper-detection heatmaps and risk evaluation',
    hi: 'छेड़छाड़ पहचान हीटमैप और जोखिम मूल्यांकन की समीक्षा करें',
  },
  'step.5': {
    en: '5. Investigate & Decide',
    hi: '5. जांच और निर्णय (Investigate & Decide)',
  },
  'step.5.desc': {
    en: 'Record officer findings, notes, and final status',
    hi: 'अधिकारी निष्कर्ष, नोट्स और अंतिम स्थिति दर्ज करें',
  },
  'step.6': {
    en: '6. Final Dossier',
    hi: '6. अंतिम रिपोर्ट (Final Dossier)',
  },
  'step.6.desc': {
    en: 'Export cryptographically verifiable PDF evidentiary report',
    hi: 'प्रमाणित और डिजिटल हस्ताक्षरित पीडीएफ रिपोर्ट डाउनलोड करें',
  },

  // Traffic Light Meanings
  'traffic.clear': {
    en: 'CLEAR — Routine Processing',
    hi: 'स्वीकृत (CLEAR) — सामान्य प्रक्रिया',
  },
  'traffic.clear.meaning': {
    en: 'No signs of tampering, font alterations, or check-digit math mismatches were detected.',
    hi: 'छेड़छाड़, फॉन्ट परिवर्तन या चेक-डिजिट विसंगति का कोई संकेत नहीं मिला।',
  },
  'traffic.clear.not_meaning': {
    en: 'Does not guarantee physical document authenticity or absence of sophisticated counterfeit paper.',
    hi: 'यह भौतिक दस्तावेज़ के असली होने या उच्च स्तरीय जाली कागज न होने की पूर्ण गारंटी नहीं देता।',
  },
  'traffic.clear.action': {
    en: 'Proceed with routine verification or border clearance per standard operating procedure.',
    hi: 'मानक संचालन प्रक्रिया के अनुसार नियमित सत्यापन या सीमा निकासी के साथ आगे बढ़ें।',
  },

  'traffic.review': {
    en: 'REVIEW — Manual Verification Recommended',
    hi: 'समीक्षा आवश्यक (REVIEW) — मानवीय सत्यापन अनुशंसित',
  },
  'traffic.review.meaning': {
    en: 'Inconsistencies, image blur, or low OCR confidences require officer inspection.',
    hi: 'अस्पष्ट छवि, कम ओसीआर सटीकता या विसंगतियों के कारण मानवीय निरीक्षण आवश्यक है।',
  },
  'traffic.review.not_meaning': {
    en: 'Does not mean the document is fraudulent; poor camera lighting or glare frequently causes this.',
    hi: 'इसका अर्थ यह नहीं है कि दस्तावेज़ फर्जी है; खराब प्रकाश या चमक से भी ऐसा हो सकता है।',
  },
  'traffic.review.action': {
    en: 'Inspect physical document against screen, re-take scan in good lighting, or interview traveler.',
    hi: 'स्क्रीन से मूल दस्तावेज़ का मिलान करें, अच्छे प्रकाश में पुनः स्कैन करें, या यात्री से पूछताछ करें।',
  },

  'traffic.high_risk': {
    en: 'HIGH RISK — Potential Alteration Detected',
    hi: 'उच्च जोखिम (HIGH RISK) — संभावित छेड़छाड़ चिह्नित',
  },
  'traffic.high_risk.meaning': {
    en: 'Significant anomalies detected (e.g. invalid passport security check digits, ELA tampering, or modified fonts).',
    hi: 'महत्वपूर्ण विसंगतियां पाई गईं (जैसे गलत पासपोर्ट चेक-डिजिट, ईएलए छेड़छाड़, या बदले हुए फॉन्ट)।',
  },
  'traffic.high_risk.not_meaning': {
    en: 'Not an automated refusal; the system flags computational anomalies for human investigation.',
    hi: 'यह स्वतः प्रवेश अस्वीकृति नहीं है; प्रणाली केवल मानवीय जांच हेतु विसंगतियों को चिह्नित करती है।',
  },
  'traffic.high_risk.action': {
    en: 'Escalate to Senior Reviewer, create an Investigation Case, and conduct secondary security screening.',
    hi: 'वरिष्ठ समीक्षक को अग्रेषित करें, जांच मामला खोलें, और द्वितीयक सुरक्षा जांच करें।',
  },

  // Common Actions
  'action.what_next': {
    en: 'Recommended Next Action',
    hi: 'अनुशंसित अगला कदम (What Next)',
  },
  'action.show_tech': {
    en: 'Show Technical Details',
    hi: 'तकनीकी विवरण देखें (Show Technical Details)',
  },
  'action.hide_tech': {
    en: 'Hide Technical Details',
    hi: 'तकनीकी विवरण छिपाएं (Hide Technical Details)',
  },
  'action.export_pdf': {
    en: 'Export Dossier PDF',
    hi: 'दस्तावेज़ पीडीएफ डाउनलोड करें (Export PDF)',
  },
  'action.create_case': {
    en: 'Create Investigation Case',
    hi: 'जांच मामला दर्ज करें (Create Case)',
  },
  'action.back_to_queue': {
    en: 'Back to Case Queue',
    hi: 'मामला सूची पर वापस जाएं (Back to Queue)',
  },
};
