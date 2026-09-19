# BSL Safety Intelligence - Mobile App (React Native / Expo)

Mobile incident reporting client designed for Bokaro Steel Limited workers on mobile phones.

## Features
- **1-Tap Voice Intake**: Record voice observations in Hindi, Bengali, Tamil, Telugu, English & more using device microphone (`expo-av`).
- **Compulsory Photographic / Video Proof**: Capture physical evidence with native phone camera or select from device gallery (`expo-image-picker`).
- **Safety Skip Option**: Instant skip to verification if taking a photo puts the worker in physical danger.
- **Adaptive Verification Interview**: Step-by-step questions dynamically generated from Bokaro SOPs with voice playback.
- **Precautionary Safety SOPs**: Localized immediate action directives with native speech playback.
- **Plant Server IP Configurator**: Change the backend server address anytime without rebuilding the app.

## How to Run on Your Mobile Phone

1. Make sure your phone and computer are connected to the same Wi-Fi network.
2. Install the **Expo Go** app on your phone:
   - [Android (Google Play Store)](https://play.google.com/store/apps/details?id=host.exp.exponent)
   - [iOS (Apple App Store)](https://apps.apple.com/app/expo-go/id982107779)
3. In this directory (`mobile/`), start the Expo development server:
   ```bash
   npx expo start
   ```
4. Scan the QR code displayed in your terminal using:
   - **Android**: Expo Go app camera scanner.
   - **iOS**: Native iPhone Camera app.
5. In the app, tap **"⚙️ Configure Plant Server IP"** if you need to point to your computer's local IP (e.g. `http://10.12.3.58:8000`).
