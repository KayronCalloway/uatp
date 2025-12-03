# UATP JavaScript/TypeScript SDK

> Official JavaScript/TypeScript SDK for UATP civilization-grade AI attribution infrastructure

## 🚀 Features

- **Simple Attribution Tracking** - Track AI interactions across platforms
- **Real-time Economic Attribution** - Earn rewards for contributions  
- **Constitutional Governance** - Participate in democratic decision-making
- **Zero-knowledge Privacy** - Privacy-preserving proofs and anonymization
- **C2PA Content Credentials** - Industry-standard content authentication
- **2025 Breakthrough Watermarking** - Meta Stable Signature, IMATAG, SynthID compatibility
- **Global Federation** - Connect to planetary-scale coordination network

## 📦 Installation

```bash
npm install @uatp/sdk
# or
yarn add @uatp/sdk
```

## 🎯 Quick Start

```typescript
import { UATP } from '@uatp/sdk';

// Initialize UATP client
const client = new UATP({
  apiKey: 'your-api-key-here'
});

// Track AI interaction with attribution
const result = await client.trackAiInteraction({
  prompt: 'Explain quantum computing',
  response: 'Quantum computing uses quantum mechanics...',
  platform: 'openai',
  model: 'gpt-4'
});

console.log('Attribution result:', result);

// Get attribution rewards
const rewards = await client.getAttributionRewards('user-123');
console.log('Total earned:', rewards.totalEarned);

// Participate in governance
await client.participateInGovernance({
  action: 'vote',
  proposalId: 'prop-456',
  vote: 'approve'
});
```

## 🛠️ Core Modules

### Attribution Tracking

```typescript
// Track AI interactions
const attribution = await client.attribution.trackInteraction({
  prompt: 'Write a poem about AI',
  response: 'In circuits deep and code so bright...',
  platform: 'anthropic',
  model: 'claude-3-5-sonnet',
  userId: 'user-456'
});

// Verify attribution integrity
const verification = await client.attribution.verifyAttribution(attribution.attributionId);
```

### Economic Engine

```typescript
// Get global economic metrics
const metrics = await client.economics.getGlobalMetrics();
console.log('Commons fund balance:', metrics.commonsFundBalance);

// Calculate attribution value
const value = await client.economics.calculateAttributionValue({
  contentType: 'text',
  contentSize: 1500,
  qualityScore: 0.9
});
```

### Governance Participation

```typescript
// Get active proposals
const proposals = await client.governance.getActiveProposals();

// Cast vote on proposal
await client.governance.castVote('proposal-123', 'approve', 'Supporting this initiative');

// Create new proposal
await client.governance.createProposal({
  title: 'Improve Attribution Accuracy',
  description: 'Proposal to enhance semantic analysis...',
  proposalType: 'technical'
});
```

### Privacy & Zero-Knowledge

```typescript
// Create privacy proof
const proof = await client.privacy.createProof({
  data: { userId: 'user-123', contribution: 'significant' },
  proofType: 'attribution'
});

// Verify proof
const verification = await client.privacy.verifyProof(proof);

// Anonymize sensitive data
const anonymized = await client.privacy.anonymizeData({
  data: userData,
  anonymizationLevel: 'standard'
});
```

### Watermarking

```typescript
// Apply 2025 breakthrough watermarking
const watermark = await client.watermarking.applyWatermark(
  'This is AI-generated content',
  'text'
);

// Detect watermarks
const detections = await client.watermarking.detectWatermark({
  content: suspiciousContent,
  contentType: 'image'
});

// Verify watermark authenticity
const verification = await client.watermarking.verifyWatermark({
  watermarkId: watermark.watermarkId
});
```

### Global Federation

```typescript
// Get network status
const status = await client.federation.getNetworkStatus();
console.log(`${status.activeNodes}/${status.totalNodes} nodes active`);

// Join federation (for node operators)
await client.federation.joinFederation({
  nodeName: 'My UATP Node',
  endpoint: 'https://my-node.example.com',
  region: 'us-west-2',
  country: 'US',
  capabilities: ['attribution', 'governance', 'privacy']
});
```

## ⚙️ Configuration

```typescript
const client = new UATP({
  apiKey: 'your-api-key',
  baseUrl: 'https://api.uatp.global', // Optional: custom endpoint
  timeout: 30000, // Optional: request timeout in ms
  retryAttempts: 3, // Optional: retry failed requests
  enablePrivacy: true, // Optional: enable zero-knowledge features
  enableWatermarking: true, // Optional: enable watermarking
  enableGovernance: true, // Optional: enable governance participation
  federationNode: 'regional.uatp.network' // Optional: specific federation node
});
```

## 📊 Event Handling

```typescript
// Listen for attribution events
client.on('attribution_tracked', (event) => {
  console.log('New attribution:', event.data.attributionId);
});

// Listen for governance events
client.on('vote_cast', (event) => {
  console.log('Vote cast:', event.data);
});

// Listen for economic events
client.on('rewards_retrieved', (event) => {
  console.log('Rewards updated:', event.data.totalEarned);
});
```

## 🔧 Advanced Usage

### Custom HTTP Client Configuration

```typescript
import axios from 'axios';

// Create client with custom axios config
const client = new UATP({
  apiKey: 'your-key',
  // Custom HTTP client configuration will be merged
});

// Access underlying HTTP client for advanced usage
client.request('POST', '/custom-endpoint', customData);
```

### Environment Support Detection

```typescript
import { checkEnvironmentSupport } from '@uatp/sdk';

const support = checkEnvironmentSupport();
if (!support.supportsZeroKnowledge) {
  console.warn('Zero-knowledge features not available in this environment');
}
```

## 🌐 Browser Support

The SDK works in both Node.js and browser environments:

- **Node.js**: 16.0.0+
- **Browsers**: Modern browsers with ES2020 support
- **React Native**: Supported with appropriate polyfills
- **Electron**: Fully supported

## 📚 API Reference

For complete API documentation, visit: [https://docs.uatp.org/sdk/javascript](https://docs.uatp.org/sdk/javascript)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📖 Documentation: [https://docs.uatp.org](https://docs.uatp.org)
- 🐛 Issues: [GitHub Issues](https://github.com/uatp/sdk-javascript/issues)
- 💬 Discord: [UATP Community](https://discord.gg/uatp)
- 📧 Email: support@uatp.org

---

**Powering the future of AI attribution and democratic governance** 🌟