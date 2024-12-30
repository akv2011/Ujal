// app/create-post/page.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { InputForm } from '@/components/InputForm';
import Share from '@/components/Share';
import { useClerk } from '@clerk/nextjs';
import HorizontalLinearStepper from '@/components/MultiStep';
import ImageGen from '@/components/ImageGen';

function Page() {
  const [resImage, setResImage] = useState<string | null>(null);
  const [resText, setText] = useState<string | null>(null);
  const [resTextGemma, setTextGemma] = useState<string | null>(null);
  const { user } = useClerk();
  const [activeStep, setActiveStep] = useState(0);
  const [shared, setShared] = useState(false);

  useEffect(() => {
    if (resText && resTextGemma) {
      setActiveStep(1);
    }
  }, [resText, resTextGemma]);

  const handleImageEncoded = (encodedImageUrl: string) => {
    setResImage(encodedImageUrl);
    setActiveStep(2);
  };

  useEffect(() => {
    if (shared) {
      setActiveStep(3);
    }
  }, [shared]);

  const stepContent = [
    <InputForm key="step1" setText={setText} setTextGemma={setTextGemma} />,
    <ImageGen
      key="step2"
      text={resText || null}
      textGemma={resTextGemma || null}
      onImageEncoded={handleImageEncoded}
    />,
    <Share
      key="step3"
      imageURL={resImage || ''}
      setShared={setShared}
      resText={resText || ''}
    />,
  ];

  if (!user) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center -mt-[150px]">
          <h1 className="text-2xl font-bold">Please sign in to continue</h1>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center">
      <HorizontalLinearStepper
        activeStep={activeStep}
        stepContent={stepContent}
      />
    </div>
  );
}

export default Page;