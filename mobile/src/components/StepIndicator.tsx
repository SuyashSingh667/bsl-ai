import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

interface StepIndicatorProps {
  currentStep: number;
}

const STEPS = [
  { step: 1, label: 'Intake' },
  { step: 2, label: 'Media' },
  { step: 3, label: 'Verify' },
  { step: 4, label: 'Safety' },
];

export const StepIndicator: React.FC<StepIndicatorProps> = ({ currentStep }) => {
  return (
    <View style={styles.container}>
      {STEPS.map((s, idx) => {
        const isCompleted = currentStep > s.step;
        const isActive = currentStep === s.step;
        return (
          <React.Fragment key={s.step}>
            <View style={styles.stepItem}>
              <View
                style={[
                  styles.circle,
                  isCompleted && styles.circleCompleted,
                  isActive && styles.circleActive,
                ]}
              >
                <Text style={[styles.circleText, (isActive || isCompleted) && styles.circleTextActive]}>
                  {isCompleted ? '✓' : s.step}
                </Text>
              </View>
              <Text style={[styles.label, isActive && styles.labelActive]}>{s.label}</Text>
            </View>
            {idx < STEPS.length - 1 && (
              <View style={[styles.line, isCompleted && styles.lineCompleted]} />
            )}
          </React.Fragment>
        );
      })}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: '#0c1626',
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
  },
  stepItem: {
    alignItems: 'center',
  },
  circle: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#1e293b',
    borderWidth: 1.5,
    borderColor: '#334155',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 4,
  },
  circleActive: {
    backgroundColor: '#2563eb',
    borderColor: '#60a5fa',
  },
  circleCompleted: {
    backgroundColor: '#059669',
    borderColor: '#34d399',
  },
  circleText: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '700',
  },
  circleTextActive: {
    color: '#ffffff',
  },
  label: {
    color: '#64748b',
    fontSize: 10,
    fontWeight: '600',
  },
  labelActive: {
    color: '#38bdf8',
    fontWeight: '700',
  },
  line: {
    flex: 1,
    height: 2,
    backgroundColor: '#1e293b',
    marginHorizontal: 6,
    marginBottom: 16,
  },
  lineCompleted: {
    backgroundColor: '#059669',
  },
});
