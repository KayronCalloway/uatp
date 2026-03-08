# UATP Developer Getting Started Guide

> Build the future of AI attribution with UATP's civilization-grade infrastructure

##  What You'll Build

UATP enables developers to integrate **attribution tracking**, **economic rewards**, and **democratic governance** into any application. This guide gets you up and running in 10 minutes.

##  Choose Your SDK

### Python SDK
Perfect for data science, AI platforms, and backend services.

```bash
pip install uatp-sdk
```

### JavaScript/TypeScript SDK
Ideal for web apps, Node.js services, and React applications.

```bash
npm install @uatp/sdk
```

##  5-Minute Quick Start

### Step 1: Get Your API Key

1. Visit [uatp.global/developers](https://uatp.global/developers)
2. Create a free developer account
3. Generate your API key
4. Copy your key (keep it secure!)

### Step 2: Install & Initialize

**Python:**
```python
from uatp_sdk import UATP

client = UATP(api_key="your-api-key-here")
```

**JavaScript/TypeScript:**
```typescript
import { UATP } from '@uatp/sdk';

const client = new UATP({
  apiKey: 'your-api-key-here'
});
```

### Step 3: Track Your First AI Interaction

**Python:**
```python
# Track an AI conversation for attribution
result = await client.track_ai_interaction(
    prompt="What is the capital of France?",
    response="The capital of France is Paris.",
    platform="openai",  # or "anthropic", "huggingface"
    model="gpt-4",
    user_id="user-123"  # optional
)

print(f"Attribution ID: {result.attribution_id}")
print(f"Creator reward: ${result.economic_impact['creator_reward']}")
```

**JavaScript/TypeScript:**
```typescript
// Track an AI conversation for attribution
const result = await client.trackAiInteraction({
  prompt: 'What is the capital of France?',
  response: 'The capital of France is Paris.',
  platform: 'openai', // or 'anthropic', 'huggingface'
  model: 'gpt-4',
  userId: 'user-123' // optional
});

console.log(`Attribution ID: ${result.attributionId}`);
console.log(`Creator reward: $${result.economicImpact.creatorReward}`);
```

### Step 4: Check Your Rewards

**Python:**
```python
# Get attribution rewards for a user
rewards = await client.get_attribution_rewards("user-123")
print(f"Total earned: ${rewards['total_earned']}")
print(f"Pending rewards: ${rewards['pending_rewards']}")
```

**JavaScript/TypeScript:**
```typescript
// Get attribution rewards for a user
const rewards = await client.getAttributionRewards('user-123');
console.log(`Total earned: $${rewards.totalEarned}`);
console.log(`Pending rewards: $${rewards.pendingRewards}`);
```

 **Congratulations!** You've just integrated AI attribution into your application.

##  Real-World Examples

### Chatbot Integration

Add attribution to your chatbot to reward users for valuable conversations:

**Python:**
```python
async def handle_chat_message(user_message, user_id):
    # Get AI response from your preferred platform
    ai_response = await get_ai_response(user_message)

    # Track for attribution and rewards
    attribution = await client.track_ai_interaction(
        prompt=user_message,
        response=ai_response,
        platform="openai",
        model="gpt-4",
        user_id=user_id
    )

    return {
        "response": ai_response,
        "attribution_id": attribution.attribution_id,
        "reward_earned": attribution.economic_impact["creator_reward"]
    }
```

**JavaScript/TypeScript:**
```typescript
async function handleChatMessage(userMessage: string, userId: string) {
  // Get AI response from your preferred platform
  const aiResponse = await getAiResponse(userMessage);

  // Track for attribution and rewards
  const attribution = await client.trackAiInteraction({
    prompt: userMessage,
    response: aiResponse,
    platform: 'openai',
    model: 'gpt-4',
    userId
  });

  return {
    response: aiResponse,
    attributionId: attribution.attributionId,
    rewardEarned: attribution.economicImpact.creatorReward
  };
}
```

### Content Creation Platform

Reward users for generating high-quality content:

**Python:**
```python
async def create_content(prompt, platform, model, creator_id):
    # Generate content using AI
    content = await generate_ai_content(prompt, platform, model)

    # Apply watermarking for authenticity
    watermark = await client.watermarking.apply_watermark(
        content=content,
        content_type="text",
        creator_id=creator_id
    )

    # Track attribution
    attribution = await client.track_ai_interaction(
        prompt=prompt,
        response=content,
        platform=platform,
        model=model,
        user_id=creator_id
    )

    return {
        "content": content,
        "watermark_id": watermark.watermark_id,
        "attribution_id": attribution.attribution_id,
        "estimated_value": attribution.economic_impact["estimated_value"]
    }
```

### Governance-Enabled App

Let users participate in platform decisions:

**JavaScript/TypeScript:**
```typescript
// Get active governance proposals
const proposals = await client.governance.getActiveProposals();

// Let user vote on a proposal
await client.governance.castVote(
  'proposal-123',
  'approve',
  'This will improve the platform significantly'
);

// Check user's voting power
const votingPower = await client.governance.getVotingPower('user-123');
console.log(`Voting power: ${votingPower.votingPower}`);
```

##  UI Components & Templates

### React Attribution Display

```tsx
import React, { useEffect, useState } from 'react';
import { UATP } from '@uatp/sdk';

const AttributionRewards: React.FC<{ userId: string }> = ({ userId }) => {
  const [rewards, setRewards] = useState(null);
  const [client] = useState(new UATP({ apiKey: process.env.REACT_APP_UATP_KEY }));

  useEffect(() => {
    const fetchRewards = async () => {
      const userRewards = await client.getAttributionRewards(userId);
      setRewards(userRewards);
    };
    fetchRewards();
  }, [userId]);

  if (!rewards) return <div>Loading rewards...</div>;

  return (
    <div className="attribution-rewards">
      <h3>Your Attribution Rewards</h3>
      <div className="reward-stat">
        <strong>${rewards.totalEarned}</strong>
        <span>Total Earned</span>
      </div>
      <div className="reward-stat">
        <strong>${rewards.pendingRewards}</strong>
        <span>Pending</span>
      </div>
      <div className="reward-stat">
        <strong>{rewards.attributionCount}</strong>
        <span>Contributions</span>
      </div>
    </div>
  );
};
```

### Vue.js Governance Panel

```vue
<template>
  <div class="governance-panel">
    <h3>Active Proposals</h3>
    <div v-for="proposal in proposals" :key="proposal.proposalId" class="proposal-card">
      <h4>{{ proposal.title }}</h4>
      <p>{{ proposal.description }}</p>
      <div class="voting-actions">
        <button @click="vote(proposal.proposalId, 'approve')" :disabled="hasVoted(proposal.proposalId)">
          Approve ({{ proposal.votesApprove }})
        </button>
        <button @click="vote(proposal.proposalId, 'reject')" :disabled="hasVoted(proposal.proposalId)">
          Reject ({{ proposal.votesReject }})
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { UATP } from '@uatp/sdk';

const client = new UATP({ apiKey: import.meta.env.VITE_UATP_KEY });
const proposals = ref([]);
const userVotes = ref(new Set());

onMounted(async () => {
  proposals.value = await client.governance.getActiveProposals();
});

const vote = async (proposalId, choice) => {
  await client.governance.castVote(proposalId, choice);
  userVotes.value.add(proposalId);
};

const hasVoted = (proposalId) => userVotes.value.has(proposalId);
</script>
```

##  Advanced Configuration

### Production Configuration

**Python:**
```python
# Production setup with retry and caching
from uatp_sdk import UATP, UATPConfig

config = UATPConfig(
    api_key=os.environ["UATP_API_KEY"],
    base_url="https://api.uatp.global",
    timeout=30,
    retry_attempts=5,
    enable_privacy=True,
    enable_watermarking=True,
    enable_governance=True,
    federation_node="us-east-1.uatp.network"
)

client = UATP(config=config)
```

**JavaScript/TypeScript:**
```typescript
// Production setup with event handling
const client = new UATP({
  apiKey: process.env.UATP_API_KEY!,
  baseUrl: 'https://api.uatp.global',
  timeout: 30000,
  retryAttempts: 5,
  enablePrivacy: true,
  enableWatermarking: true,
  enableGovernance: true,
  federationNode: 'us-east-1.uatp.network'
});

// Handle real-time events
client.on('attribution_tracked', (event) => {
  console.log('New attribution:', event.data.attributionId);
  // Update UI, send notifications, etc.
});

client.on('rewards_retrieved', (event) => {
  console.log('Rewards updated:', event.data.totalEarned);
  // Update reward display
});
```

### Error Handling Best Practices

**Python:**
```python
from uatp_sdk import UATP, UATPError

try:
    result = await client.track_ai_interaction(...)
except UATPError as e:
    if e.code == "RATE_LIMIT_EXCEEDED":
        # Handle rate limiting
        await asyncio.sleep(5)
        result = await client.track_ai_interaction(...)
    elif e.code == "INSUFFICIENT_BALANCE":
        # Handle payment issues
        print(f"Add funds to continue: {e.message}")
    else:
        # Log and handle other errors
        logger.error(f"UATP error: {e.code} - {e.message}")
        raise
```

**JavaScript/TypeScript:**
```typescript
try {
  const result = await client.trackAiInteraction(...);
} catch (error) {
  if (error instanceof UATPError) {
    switch (error.code) {
      case 'RATE_LIMIT_EXCEEDED':
        // Wait and retry
        await new Promise(resolve => setTimeout(resolve, 5000));
        return await client.trackAiInteraction(...);

      case 'INSUFFICIENT_BALANCE':
        // Handle payment
        console.log(`Add funds to continue: ${error.message}`);
        break;

      default:
        console.error(`UATP error: ${error.code} - ${error.message}`);
        throw error;
    }
  } else {
    // Handle network or other errors
    console.error('Network error:', error.message);
    throw error;
  }
}
```

##  Next Steps

Now that you have the basics working, explore these advanced features:

1. **[Zero-Knowledge Privacy](./privacy-guide.md)** - Protect user data with mathematical proofs
2. **[Watermarking Integration](./watermarking-guide.md)** - Embed provenance in content
3. **[Governance Participation](./governance-guide.md)** - Build democratic features
4. **[Federation Scaling](./federation-guide.md)** - Connect to global networks
5. **[Economic Models](./economics-guide.md)** - Design reward systems

##  Get Help

-  **Full Documentation**: [docs.uatp.org](https://docs.uatp.org)
-  **Discord Community**: [discord.gg/uatp](https://discord.gg/uatp)
-  **Report Issues**: [github.com/KayronCalloway/sdk/issues](https://github.com/KayronCalloway/sdk/issues)
-  **Email Support**: developers@uatp.org

**Ready to build the future?** Start with the [Example Applications](./examples/) or dive into the [Complete API Reference](./api-reference/).

---

*Building attribution infrastructure for human-AI collaboration at civilization scale*
