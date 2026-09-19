/**
 * Internationalization (i18n) Service for BSL AI Mobile App.
 *
 * Supports 4 key heavy metallurgy languages across the Bokaro / Eastern Industrial belt:
 *   - 'hi': Hindi (हिन्दी) - Primary operational language
 *   - 'en': Indian English - Technical & administrative language
 *   - 'bn': Bengali (বাংলা) - Widely spoken in Bokaro/Durgapur/Burnpur plants
 *   - 'or': Odia (ଓଡ଼ିଆ) - Rourkela/Bokaro mining & metallurgy corridor
 *
 * Note: Includes honest operational disclaimer on regional language dialect limits.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

export type SupportedLanguage = 'hi' | 'en' | 'bn' | 'or';

const LANG_STORAGE_KEY = '@bsl_ai_selected_language_v1';

export const LANGUAGE_METADATA: Record<SupportedLanguage, { label: string; nativeName: string; flag: string }> = {
  hi: { label: 'Hindi', nativeName: 'हिन्दी', flag: '' },
  en: { label: 'English', nativeName: 'English', flag: '' },
  bn: { label: 'Bengali', nativeName: 'বাংলা', flag: '' },
  or: { label: 'Odia', nativeName: 'ଓଡ଼ିଆ', flag: '' },
};

const STRINGS: Record<SupportedLanguage, Record<string, string>> = {
  hi: {
    appTitle: 'BSL AI सुरक्षा प्रणाली',
    appSubtitle: 'सेल-बोकारो इस्पात संयंत्र औद्योगिक सुरक्षा',
    emergencyButton: 'आपातकालीन खतरा (Emergency)',
    emergencyDesc: 'सक्रिय आग, गैस रिसाव, या जीवन जोखिम — तुरंत कार्रवाई',
    suspectedButton: 'संदिग्ध खतरा / नियर-मिस',
    suspectedDesc: 'अनियमित कंपन, सुरक्षा उल्लंघन, या संभावित जोखिम',
    recordVoice: 'बोलकर रिपोर्ट दर्ज करें (Voice First)',
    tapToSpeak: 'बोलने के लिए माइक दबाएं',
    recordingActive: 'आवाज़ रिकॉर्ड हो रही है... पूरा होने पर फिर दबाएं',
    confirmTranscript: 'ट्रांसक्रिप्ट की पुष्टि करें:',
    confirmButton: 'पुष्टि करें और आगे बढ़ें ➔',
    editTranscript: 'संशोधित करें',
    offlineBanner: 'ऑफ़लाइन मोड: रिपोर्ट कतार में सुरक्षित है, नेटवर्क मिलने पर सिंक होगी',
    sosFallbackAlert: 'नेटवर्क अनुपलब्ध! कंट्रोल रूम को सीधा SMS भेजा जा रहा है...',
    dialectNotice: 'क्षेत्रीय भाषा प्रोटोटाइप: तकनीकी इस्पात संयंत्र शब्दावली की सटीकता बोकारो फील्ड कर्मियों के साथ परीक्षण योग्य है।',
    sopChecklist: 'अनिवार्य सुरक्षा सावधानियां (SOP Checklist)',
    markDone: 'पूरा हुआ चिन्हित करें',
    readAloud: 'पूरा चेकलिस्ट सुनें (Audio Briefing)',
  },
  en: {
    appTitle: 'BSL AI Safety Platform',
    appSubtitle: 'SAIL-Bokaro Steel Plant Industrial Safety',
    emergencyButton: 'Critical Emergency (Fast-Path)',
    emergencyDesc: 'Active fire, toxic gas leak, or immediate life risk',
    suspectedButton: 'Suspected Hazard / Near-Miss',
    suspectedDesc: 'Abnormal vibration, minor leak, or PPE non-compliance',
    recordVoice: 'Record Incident Voice Note',
    tapToSpeak: 'Tap Giant Microphone to Speak',
    recordingActive: 'Recording speech... Tap button again when finished',
    confirmTranscript: 'Confirm Speech Transcript:',
    confirmButton: 'Confirm & Continue ➔',
    editTranscript: 'Edit Transcript',
    offlineBanner: 'Offline Mode: Report stored in persistent outbox; auto-syncs when online',
    sosFallbackAlert: 'Network unreachable! Dispatching emergency SMS to Bokaro Control Room...',
    dialectNotice: 'Regional Language Scaffolding: Dialect accuracy for heavy metallurgy jargon requires on-site validation with Bokaro shift workers.',
    sopChecklist: 'Mandatory Safety SOP Checklist',
    markDone: 'Mark Completed',
    readAloud: 'Read Complete Checklist Aloud',
  },
  bn: {
    appTitle: 'BSL AI নিরাপত্তা ব্যবস্থা',
    appSubtitle: 'সেল-বোকারো ইস্পাত কারখানা শিল্প নিরাপত্তা',
    emergencyButton: 'জরুরী বিপত্তি (Emergency)',
    emergencyDesc: 'সক্রিয় আগুন, বিষাক্ত গ্যাস লিকেজ, বা জীবনের ঝুঁকি',
    suspectedButton: 'সন্দেহজনক বিপদ / নিয়ার-মিস',
    suspectedDesc: 'অনিয়মিত কম্পন, ক্ষুদ্র লিকেজ বা সম্ভাব্য বিপত্তি',
    recordVoice: 'কথা বলে রিপোর্ট করুন (Voice First)',
    tapToSpeak: 'কথা বলতে বোতাম টিপুন',
    recordingActive: 'রেকর্ডিং চলছে... শেষ হলে আবার টিপুন',
    confirmTranscript: 'ট্রান্সক্রিপ্ট নিশ্চিত করুন:',
    confirmButton: 'নিশ্চিত করুন এবং এগিয়ে যান ➔',
    editTranscript: 'সম্পাদনা করুন',
    offlineBanner: 'অফলাইন মোড: রিপোর্ট আউটবক্সে সংরক্ষিত আছে, সংযোগ ফিরলে সিঙ্ক হবে',
    sosFallbackAlert: 'নেটওয়ার্ক বিচ্ছিন্ন! কন্ট্রোল রুমে জরুরী SMS পাঠানো হচ্ছে...',
    dialectNotice: 'আঞ্চলিক ভাষা যাচাইকরণ: ইস্পাত কারখানার আঞ্চলিক প্রযুক্তিগত পরিভাষার নির্ভুলতা বোকারো শিফট কর্মীদের সাথে মাঠপর্যায়ে পরীক্ষা প্রয়োজন।',
    sopChecklist: 'বাধ্যতামূলক নিরাপত্তা নির্দেশাবলী (SOP)',
    markDone: 'সম্পন্ন চিহ্নিত করুন',
    readAloud: 'সম্পূর্ণ নির্দেশাবলী শুনুন',
  },
  or: {
    appTitle: 'BSL AI ସୁରକ୍ଷା ପ୍ରଣାଳୀ',
    appSubtitle: 'ସେଲ୍-ବୋକାରୋ ଇସ୍ପାତ କାରଖାନା ଶିଳ୍ପ ସୁରକ୍ଷା',
    emergencyButton: 'ଜରୁରୀକାଳୀନ ବିପଦ (Emergency)',
    emergencyDesc: 'ସକ୍ରିୟ ନିଆଁ, ବିଷାକ୍ତ ଗ୍ୟାସ ଲିକେଜ୍, କିମ୍ବା ଜୀବନ ପ୍ରତି ବିପଦ',
    suspectedButton: 'ସନ୍ଦିଗ୍ଧ ବିପଦ / ନିୟର-ମିସ୍',
    suspectedDesc: 'ଅସ୍ୱାଭାବିକ କମ୍ପନ, ସୁରକ୍ଷା ନିୟମ ଉଲ୍ଲଂଘନ କିମ୍ବା ସମ୍ଭାବ୍ୟ ବିପଦ',
    recordVoice: 'କଥା ହୋଇ ରିପୋର୍ଟ କରନ୍ତୁ (Voice First)',
    tapToSpeak: 'କହିବା ପାଇଁ ମାଇକ୍ ଦବାନ୍ତୁ',
    recordingActive: 'ଭଏସ୍ ରେକର୍ଡିଂ ଚାଲିଛି... ଶେଷ ହେଲେ ପୁଣି ଦବାନ୍ତୁ',
    confirmTranscript: 'ଟ୍ରାନ୍ସକ୍ରିପ୍ଟ ନିଶ୍ଚିତ କରନ୍ତୁ:',
    confirmButton: 'ନିଶ୍ଚିତ କରନ୍ତୁ ଏବଂ ଆଗକୁ ବଢ଼ନ୍ତୁ ➔',
    editTranscript: 'ସଂଶୋଧନ କରନ୍ତୁ',
    offlineBanner: 'ଅଫଲାଇନ୍ ମୋଡ୍: ରିପୋର୍ଟ ସୁରକ୍ଷିତ ଭାବେ ରହିଛି, ନେଟୱର୍କ ଆସିଲେ ସିଙ୍କ୍ ହେବ',
    sosFallbackAlert: 'ନେଟୱର୍କ ନାହିଁ! କଣ୍ଟ୍ରୋଲ୍ ରୁମକୁ ଜରୁରୀକାଳୀନ SMS ପଠାଯାଉଛି...',
    dialectNotice: 'ଆଞ୍ଚଳିକ ଭାଷା ପ୍ରମାଣୀକରଣ: ଇସ୍ପାତ କାରଖାନାର ବୈଷୟିକ ଶବ୍ଦାବଳୀ ପାଇଁ ବୋକାରୋ ଶିଫ୍ଟ କର୍ମଚାରୀଙ୍କ ସହିତ କ୍ଷେତ୍ରସ୍ତରୀୟ ପରୀକ୍ଷା ଆବଶ୍ୟକ।',
    sopChecklist: 'ବାଧ୍ୟତାମୂଳକ ସୁରକ୍ଷା ନିର୍ଦ୍ଦେଶାବଳୀ (SOP)',
    markDone: 'ସମ୍ପନ୍ନ ଚିହ୍ନିତ କରନ୍ତୁ',
    readAloud: 'ସମ୍ପୂର୍ଣ୍ଣ ନିର୍ଦ୍ଦେଶ ଶୁଣନ୍ତୁ',
  },
};

class I18nManager {
  private currentLang: SupportedLanguage = 'hi';
  private listeners: Set<(lang: SupportedLanguage) => void> = new Set();

  constructor() {
    this.init();
  }

  private async init() {
    try {
      const saved = await AsyncStorage.getItem(LANG_STORAGE_KEY);
      if (saved && saved in LANGUAGE_METADATA) {
        this.currentLang = saved as SupportedLanguage;
        this.notify();
      }
    } catch (e) {}
  }

  getLanguage(): SupportedLanguage {
    return this.currentLang;
  }

  async setLanguage(lang: SupportedLanguage): Promise<void> {
    if (lang in LANGUAGE_METADATA) {
      this.currentLang = lang;
      await AsyncStorage.setItem(LANG_STORAGE_KEY, lang);
      this.notify();
    }
  }

  t(key: string, fallback?: string): string {
    const dict = STRINGS[this.currentLang] || STRINGS['hi'];
    return dict[key] || STRINGS['en']?.[key] || fallback || key;
  }

  subscribe(cb: (lang: SupportedLanguage) => void): () => void {
    this.listeners.add(cb);
    cb(this.currentLang);
    return () => {
      this.listeners.delete(cb);
    };
  }

  private notify() {
    for (const l of this.listeners) {
      try {
        l(this.currentLang);
      } catch (e) {}
    }
  }
}

export const i18n = new I18nManager();
