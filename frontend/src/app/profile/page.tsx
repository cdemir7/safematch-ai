import { OnboardingProvider } from "@/components/onboarding/OnboardingContext";
import { StepWizardLayout } from "@/components/onboarding/StepWizardLayout";

export default function ProfilePage() {
  return (
    <OnboardingProvider>
      <StepWizardLayout />
    </OnboardingProvider>
  );
}
