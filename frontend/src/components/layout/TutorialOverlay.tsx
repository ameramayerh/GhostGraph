import React, { useState, useEffect } from 'react';
import { X, ChevronRight, ChevronLeft, ShieldCheck, Target, Activity, Settings, Cpu } from 'lucide-react';

interface TutorialOverlayProps {
  onClose: () => void;
}

export const TutorialOverlay: React.FC<TutorialOverlayProps> = ({ onClose }) => {
  const [step, setStep] = useState(0);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Small delay for entrance animation
    setTimeout(() => setIsVisible(true), 100);
  }, []);

  const steps = [
    {
      title: "Welcome to GhostGraph",
      description: "Your AI-powered continuous security validation platform. Let's take a quick tour of how to operate the system.",
      icon: <ShieldCheck className="w-12 h-12 text-cyan-400 mb-4" />,
      highlightId: null
    },
    {
      title: "1. Define Engagements",
      description: "Start by creating a New Engagement. This defines the scope of your scan (e.g. domain name, API URL) and ensures you have proper authorization.",
      icon: <Target className="w-12 h-12 text-blue-400 mb-4" />,
      highlightId: "nav-engagements"
    },
    {
      title: "2. Scan Your Source Code",
      description: "Inside an active engagement, upload a ZIP file using 'Upload & Scan Source ZIP'. GhostGraph checks dependencies, source-code patterns, and important authentication or route files.",
      icon: <Activity className="w-12 h-12 text-red-400 mb-4" />,
      highlightId: "btn-upload-scan"
    },
    {
      title: "3. AI Threat Remediation",
      description: "When vulnerabilities are found, click 'Analyze with AI'. GhostGraph's LLM engine contextualizes the threat and generates code-level patches.",
      icon: <Cpu className="w-12 h-12 text-purple-400 mb-4" />,
      highlightId: "btn-ai-analyze"
    },
    {
      title: "4. Configure Your LLMs",
      description: "Don't forget to configure your API keys in the Settings page so the AI engine can assist you with remediation.",
      icon: <Settings className="w-12 h-12 text-gray-400 mb-4" />,
      highlightId: "nav-settings"
    }
  ];

  const handleNext = () => {
    if (step < steps.length - 1) {
      setStep(step + 1);
    } else {
      closeTutorial();
    }
  };

  const handlePrev = () => {
    if (step > 0) setStep(step - 1);
  };

  const closeTutorial = () => {
    setIsVisible(false);
    setTimeout(onClose, 300); // Wait for exit animation
  };

  const currentStep = steps[step];

  return (
    <div className={`fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm transition-opacity duration-300 ${isVisible ? 'opacity-100' : 'opacity-0'}`}>
      
      {/* Spotlight Effect (Simulated) */}
      <div className="absolute inset-0 pointer-events-none radial-gradient-spotlight"></div>

      <div className={`relative bg-gray-900 border border-gray-700 shadow-2xl shadow-cyan-500/20 rounded-2xl w-full max-w-lg p-8 transform transition-all duration-500 ${isVisible ? 'scale-100 translate-y-0' : 'scale-95 translate-y-8'}`}>
        
        {/* Close Button */}
        <button 
          onClick={closeTutorial}
          className="absolute top-4 right-4 p-2 text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 rounded-full transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Content */}
        <div className="flex flex-col items-center text-center mt-4">
          <div className="animate-float">
            {currentStep.icon}
          </div>
          <h2 className="text-2xl font-bold text-white mb-3 tracking-tight">
            {currentStep.title}
          </h2>
          <p className="text-gray-300 leading-relaxed mb-8">
            {currentStep.description}
          </p>
        </div>

        {/* Progress Dots */}
        <div className="flex justify-center space-x-2 mb-8">
          {steps.map((_, i) => (
            <div 
              key={i} 
              className={`h-2 rounded-full transition-all duration-300 ${i === step ? 'w-8 bg-cyan-500' : 'w-2 bg-gray-700'}`}
            />
          ))}
        </div>

        {/* Navigation Buttons */}
        <div className="flex justify-between items-center border-t border-gray-800 pt-6">
          <button 
            onClick={handlePrev}
            disabled={step === 0}
            className={`flex items-center px-4 py-2 rounded-lg font-medium transition-colors ${step === 0 ? 'text-gray-600 cursor-not-allowed' : 'text-gray-300 hover:bg-gray-800'}`}
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Previous
          </button>
          
          <button 
            onClick={handleNext}
            className="flex items-center px-6 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg font-medium shadow-lg shadow-cyan-500/30 transition-all hover:scale-105"
          >
            {step === steps.length - 1 ? 'Get Started' : 'Next'}
            {step !== steps.length - 1 && <ChevronRight className="w-4 h-4 ml-1" />}
          </button>
        </div>
      </div>
    </div>
  );
};
