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
    paddingVertical: 14,
    paddingHorizontal: 20,
    backgroundColor: '#000000',
    borderBottomWidth: 0.5,
    borderBottomColor: 'rgba(255, 255, 255, 0.12)',
  },
  stepItem: {
    alignItems: 'center',
  },
  circle: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#1c1c1e',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 4,
  },
  circleActive: {
    backgroundColor: '#0A84FF',
    borderColor: '#0A84FF',
  },
  circleCompleted: {
    backgroundColor: '#30D158',
    borderColor: '#30D158',
  },
  circleText: {
    color: 'rgba(235, 235, 245, 0.6)',
    fontSize: 12,
    fontWeight: '700',
  },
  circleTextActive: {
    color: '#ffffff',
  },
  label: {
    color: 'rgba(235, 235, 245, 0.45)',
    fontSize: 11,
    fontWeight: '500',
    letterSpacing: -0.2,
  },
  labelActive: {
    color: '#0A84FF',
    fontWeight: '600',
  },
  line: {
    flex: 1,
    height: 1.5,
    backgroundColor: 'rgba(255, 255, 255, 0.12)',
    marginHorizontal: 8,
    marginBottom: 16,
  },
  lineCompleted: {
    backgroundColor: '#30D158',
  },
});
