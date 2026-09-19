import React, { useState } from 'react';
import { SafeAreaView, StatusBar, StyleSheet, View } from 'react-native';
import { ReportTypeSelect } from './src/screens/ReportTypeSelectScreen';
import { IncidentRecorderScreen } from './src/screens/IncidentRecorderScreen';
import { MediaEvidenceScreen } from './src/screens/MediaEvidenceScreen';
import { VerificationInterviewScreen } from './src/screens/VerificationInterviewScreen';
import { PrecautionaryMeasuresScreen } from './src/screens/PrecautionaryMeasuresScreen';
import { TicketResultScreen } from './src/screens/TicketResultScreen';
import { KioskLoginScreen, KioskSession } from './src/screens/KioskLoginScreen';
import { ServerConfigModal } from './src/components/ServerConfigModal';
import { Ticket } from './src/services/api';

type WorkflowStep =
  | 'kiosk_login'
  | 'select_type'
  | 'record_incident'
  | 'media_evidence'
  | 'verification'
  | 'precautions'
  | 'result';

export default function App() {
  const [step, setStep] = useState<WorkflowStep>('select_type');
  const [reportType, setReportType] = useState<'emergency' | 'suspected'>('suspected');
  const [isAnonymous, setIsAnonymous] = useState<boolean>(false);
  const [shift, setShift] = useState<string>('Shift A');
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [kioskSession, setKioskSession] = useState<KioskSession | null>(null);
  const [showConfigModal, setShowConfigModal] = useState<boolean>(false);

  // 1. Report type selected
  const handleSelectReportType = (
    type: 'emergency' | 'suspected',
    anonymous: boolean = false,
    reportingShift: string = 'Shift A'
  ) => {
    setReportType(type);
    setIsAnonymous(anonymous);
    setShift(reportingShift);
    setStep('record_incident');
  };

  // 2. Incident created from audio or text
  const handleIncidentCreated = (newTicket: Ticket) => {
    setTicket(newTicket);
    const isEmergency = newTicket.report_type === 'emergency' || reportType === 'emergency';
    if (isEmergency) {
      // FAST-PATH: Acute emergencies immediately show personal safety directives and emergency dispatch status
      setStep('precautions');
    } else {
      // Offer optional media evidence capture (can be skipped with 1 tap)
      setStep('media_evidence');
    }
  };

  // 3. Media proof uploaded
  const handleMediaUploaded = (updatedTicket: Ticket) => {
    setTicket(updatedTicket);
    const isEmergency = updatedTicket.report_type === 'emergency' || reportType === 'emergency';
    if (isEmergency) {
      setStep('precautions');
    } else {
      setStep('verification');
    }
  };

  // 4. Skip media if worker in danger or optional skip
  const handleSkipMedia = () => {
    const isEmergency = ticket?.report_type === 'emergency' || reportType === 'emergency';
    if (isEmergency) {
      setStep('precautions');
    } else {
      setStep('verification');
    }
  };

  // 5. Verification interview complete
  const handleInterviewComplete = (finalTicket: Ticket) => {
    setTicket(finalTicket);
    setStep('precautions');
  };

  // 6. Reset to log another report
  const handleStartNewReport = () => {
    setTicket(null);
    if (kioskSession) {
      // Return to kiosk login for next worker on shared terminal
      setStep('kiosk_login');
    } else {
      setStep('select_type');
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="light-content" backgroundColor="#000000" />
      <View style={styles.container}>
        {step === 'kiosk_login' && (
          <KioskLoginScreen
            onSessionStart={(session) => {
              setKioskSession(session);
              setStep('select_type');
            }}
            onExitKiosk={() => {
              setKioskSession(null);
              setStep('select_type');
            }}
          />
        )}

        {step === 'select_type' && (
          <ReportTypeSelect
            onSelect={handleSelectReportType}
            onOpenSettings={() => setShowConfigModal(true)}
            onOpenKiosk={() => setStep('kiosk_login')}
          />
        )}

        {step === 'record_incident' && (
          <IncidentRecorderScreen
            reportType={reportType}
            isAnonymous={isAnonymous}
            shift={shift}
            onIncidentCreated={handleIncidentCreated}
            onBack={() => setStep('select_type')}
            kioskSession={kioskSession}
            onSwitchToKiosk={() => setStep('kiosk_login')}
          />
        )}

        {step === 'media_evidence' && ticket && (
          <MediaEvidenceScreen
            ticket={ticket}
            onMediaUploaded={handleMediaUploaded}
            onSkip={handleSkipMedia}
          />
        )}

        {step === 'verification' && ticket && (
          <VerificationInterviewScreen
            ticket={ticket}
            onInterviewComplete={handleInterviewComplete}
          />
        )}

        {step === 'precautions' && ticket && (
          <PrecautionaryMeasuresScreen
            ticket={ticket}
            onProceedToResult={() => setStep('result')}
          />
        )}

        {step === 'result' && ticket && (
          <TicketResultScreen
            ticket={ticket}
            onStartNewReport={handleStartNewReport}
          />
        )}

        <ServerConfigModal
          visible={showConfigModal}
          onClose={() => setShowConfigModal(false)}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#000000',
  },
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
});
