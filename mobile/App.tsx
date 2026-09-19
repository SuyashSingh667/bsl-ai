import React, { useState } from 'react';
import { SafeAreaView, StatusBar, StyleSheet, View } from 'react-native';
import { ReportTypeSelect } from './src/screens/ReportTypeSelectScreen';
import { IncidentRecorderScreen } from './src/screens/IncidentRecorderScreen';
import { MediaEvidenceScreen } from './src/screens/MediaEvidenceScreen';
import { VerificationInterviewScreen } from './src/screens/VerificationInterviewScreen';
import { PrecautionaryMeasuresScreen } from './src/screens/PrecautionaryMeasuresScreen';
import { TicketResultScreen } from './src/screens/TicketResultScreen';
import { ServerConfigModal } from './src/components/ServerConfigModal';
import { Ticket } from './src/services/api';

type WorkflowStep =
  | 'select_type'
  | 'record_incident'
  | 'media_evidence'
  | 'verification'
  | 'precautions'
  | 'result';

export default function App() {
  const [step, setStep] = useState<WorkflowStep>('select_type');
  const [reportType, setReportType] = useState<'emergency' | 'suspected'>('suspected');
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [showConfigModal, setShowConfigModal] = useState<boolean>(false);

  // 1. Report type selected
  const handleSelectReportType = (type: 'emergency' | 'suspected') => {
    setReportType(type);
    setStep('record_incident');
  };

  // 2. Incident created from audio or text
  const handleIncidentCreated = (newTicket: Ticket) => {
    setTicket(newTicket);
    const isEmergency = newTicket.report_type === 'emergency' || reportType === 'emergency';
    if (isEmergency) {
      // FAST-PATH: Acute emergencies immediately show personal safety directives and emergency dispatch status
      setStep('precautions');
    } else if (newTicket.requires_photo_proof) {
      setStep('media_evidence');
    } else {
      setStep('verification');
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

  // 4. Skip media if worker in danger
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
    setStep('select_type');
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="light-content" backgroundColor="#070d18" />
      <View style={styles.container}>
        {step === 'select_type' && (
          <ReportTypeSelect
            onSelect={handleSelectReportType}
            onOpenSettings={() => setShowConfigModal(true)}
          />
        )}

        {step === 'record_incident' && (
          <IncidentRecorderScreen
            reportType={reportType}
            onIncidentCreated={handleIncidentCreated}
            onBack={() => setStep('select_type')}
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
    backgroundColor: '#070d18',
  },
  container: {
    flex: 1,
    backgroundColor: '#070d18',
  },
});
