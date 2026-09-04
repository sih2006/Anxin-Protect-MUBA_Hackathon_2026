/** Explicit shape shared by en.ts and zh.ts. Using an interface (rather than
 * `typeof en`) means the two dictionaries are checked for *matching keys*,
 * not matching literal string values -- otherwise TypeScript would force
 * every Chinese string to literally equal its English counterpart. */
export interface Dictionary {
  app: {
    name: string;
    tagline: string;
    poweredBy: string;
  };
  nav: {
    languageLabel: string;
    switchToZh: string;
  };
  input: {
    heading: string;
    modeText: string;
    modeUrl: string;
    modeScreenshot: string;
    analysisFactCheck: string;
    analysisMeme: string;
    textPlaceholder: string;
    urlPlaceholder: string;
    uploadLabel: string;
    uploadHint: string;
    submit: string;
    submitting: string;
    cancel: string;
    charCount: (count: number, max: number) => string;
    tooLong: string;
    emptyError: string;
    invalidUrl: string;
    invalidImage: string;
    tryExample: string;
    exampleScamLabel: string;
    exampleScamText: string;
    exampleClaimLabel: string;
    exampleClaimText: string;
  };
  ocr: {
    extracting: string;
    reviewHeading: string;
    reviewHint: string;
    noTextFound: string;
    confirmAndCheck: string;
    processingFailed: string;
  };
  progress: {
    stageClaim: string;
    stageEvidence: string;
    stageModelA: string;
    stageModelB: string;
    stageConsensus: string;
    elapsed: (s: number) => string;
    stillWorking: string;
  };
  results: {
    heading: string;
    verdictCredible: string;
    verdictQuestionable: string;
    verdictHighRisk: string;
    verdictInsufficient: string;
    truthScore: string;
    truthScoreHint: string;
    riskLevel: string;
    riskLow: string;
    riskMedium: string;
    riskHigh: string;
    fraudRiskScore: string;
    fraudRiskHint: string;
    warningSignsHeading: string;
    evidenceQualityLabel: string;
    evidenceStrong: string;
    evidenceMixed: string;
    evidenceWeak: string;
    evidenceNone: string;
    confidence: string;
    confidenceHint: string;
    evidenceHeading: string;
    noEvidence: string;
    limitationsHeading: string;
    nextActionsHeading: string;
    newCheck: string;
    disagreementBadge: string;
    excerptLabel: string;
    modelComparisonHeading: string;
    modelComparisonHint: string;
    modelGap: (points: number) => string;
    modelVerdictLabel: string;
    singleModelHeading: string;
    singleModelHint: string;
    singleModelBadge: string;
  };
  transparency: {
    heading: string;
    toggleShow: string;
    toggleHide: string;
    requestedModel: string;
    actualModel: string;
    requestId: string;
    devshardId: string;
    latency: string;
    fallbackWarning: string;
    receiptLink: string;
    receiptHint: string;
    mockNotice: string;
    modelFailed: string;
  };
  meme: {
    heading: string;
    disclaimer: string;
    literal: string;
    joke: string;
    culture: string;
    safety: string;
    visualOnlyWarning: string;
  };
  errors: {
    heading: string;
    rateLimited: string;
    timeout: string;
    network: string;
    generic: string;
    retry: string;
  };
  footer: {
    disclaimer: string;
    trackNote: string;
  };
}
