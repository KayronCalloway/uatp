# UATP Developer Tutorials

> Step-by-step guides to build powerful attribution-enabled applications

##  Tutorial Series

###  **Beginner Tutorials** (30 minutes each)

1. **[Build Your First Attribution-Enabled Chat App](#tutorial-1-attribution-chat-app)**
2. **[Add Economic Rewards to User Contributions](#tutorial-2-economic-rewards)**
3. **[Create a Simple Governance Dashboard](#tutorial-3-governance-dashboard)**
4. **[Implement Privacy-Preserving Analytics](#tutorial-4-privacy-analytics)**

###  **Intermediate Tutorials** (45-60 minutes each)

5. **[Build a Content Creation Platform](#tutorial-5-content-platform)**
6. **[Integrate Watermarking for Content Authentication](#tutorial-6-watermarking-integration)**
7. **[Create a Democratic Voting System](#tutorial-7-voting-system)**
8. **[Build Cross-Platform Attribution Tracking](#tutorial-8-cross-platform-tracking)**

###  **Advanced Tutorials** (90+ minutes each)

9. **[Design a Multi-Tenant Attribution System](#tutorial-9-multi-tenant-system)**
10. **[Build a Federation Node](#tutorial-10-federation-node)**
11. **[Create an AI Rights Management Platform](#tutorial-11-ai-rights-platform)**
12. **[Implement Real-Time Attribution Analytics](#tutorial-12-realtime-analytics)**

---

## Tutorial 1: Attribution-Enabled Chat App

**Time**: 30 minutes | **Level**: Beginner | **Stack**: React + Node.js

Build a simple chat application that tracks AI interactions and rewards users for valuable conversations.

### What You'll Build

- Real-time chat interface
- AI response generation (OpenAI/Anthropic)
- Attribution tracking for each message
- User reward display
- Simple analytics dashboard

### Prerequisites

- Basic React/Node.js knowledge
- OpenAI or Anthropic API key
- UATP developer account

### Step 1: Project Setup

```bash
# Create new React app
npx create-react-app uatp-chat-app
cd uatp-chat-app

# Install dependencies
npm install @uatp/sdk openai socket.io-client
npm install -D @types/node

# Create backend directory
mkdir backend
cd backend
npm init -y
npm install express socket.io cors dotenv
```

### Step 2: Backend Setup

Create `backend/server.js`:

```javascript
const express = require('express');
const { Server } = require('socket.io');
const { UATP } = require('@uatp/sdk');
const OpenAI = require('openai');
require('dotenv').config();

const app = express();
const server = require('http').createServer(app);
const io = new Server(server, { cors: { origin: "*" } });

// Initialize clients
const uatp = new UATP({ apiKey: process.env.UATP_API_KEY });
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

app.use(express.json());
app.use(require('cors')());

// Handle chat messages
io.on('connection', (socket) => {
  console.log('User connected:', socket.id);

  socket.on('send-message', async (data) => {
    try {
      const { message, userId } = data;

      // Get AI response
      const completion = await openai.chat.completions.create({
        model: "gpt-4",
        messages: [{ role: "user", content: message }],
      });

      const aiResponse = completion.choices[0].message.content;

      // Track attribution
      const attribution = await uatp.trackAiInteraction({
        prompt: message,
        response: aiResponse,
        platform: 'openai',
        model: 'gpt-4',
        userId: userId
      });

      // Send response back
      socket.emit('ai-response', {
        message: aiResponse,
        attributionId: attribution.attributionId,
        reward: attribution.economicImpact.creatorReward,
        timestamp: new Date()
      });

    } catch (error) {
      console.error('Error:', error);
      socket.emit('error', { message: 'Failed to process message' });
    }
  });

  socket.on('get-rewards', async (userId) => {
    try {
      const rewards = await uatp.getAttributionRewards(userId);
      socket.emit('rewards-update', rewards);
    } catch (error) {
      console.error('Error getting rewards:', error);
    }
  });
});

server.listen(3001, () => {
  console.log('Server running on port 3001');
});
```

### Step 3: Frontend Chat Component

Create `src/components/ChatApp.js`:

```jsx
import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import './ChatApp.css';

const socket = io('http://localhost:3001');

const ChatApp = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [userId] = useState(`user-${Math.random().toString(36).substr(2, 9)}`);
  const [rewards, setRewards] = useState({ totalEarned: '0.0', attributionCount: 0 });
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Listen for AI responses
    socket.on('ai-response', (data) => {
      setMessages(prev => [...prev, {
        type: 'ai',
        content: data.message,
        attributionId: data.attributionId,
        reward: data.reward,
        timestamp: data.timestamp
      }]);
      setIsLoading(false);

      // Update rewards
      socket.emit('get-rewards', userId);
    });

    // Listen for rewards updates
    socket.on('rewards-update', (rewardsData) => {
      setRewards(rewardsData);
    });

    // Initial rewards fetch
    socket.emit('get-rewards', userId);

    return () => {
      socket.off('ai-response');
      socket.off('rewards-update');
    };
  }, [userId]);

  const sendMessage = () => {
    if (!inputMessage.trim() || isLoading) return;

    // Add user message
    setMessages(prev => [...prev, {
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    }]);

    // Send to backend
    socket.emit('send-message', {
      message: inputMessage,
      userId: userId
    });

    setInputMessage('');
    setIsLoading(true);
  };

  return (
    <div className="chat-app">
      <div className="chat-header">
        <h1>UATP Attribution Chat</h1>
        <div className="rewards-display">
          <span>Earned: ${rewards.totalEarned}</span>
          <span>Contributions: {rewards.attributionCount}</span>
        </div>
      </div>

      <div className="messages-container">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.type}`}>
            <div className="message-content">{msg.content}</div>
            {msg.attributionId && (
              <div className="attribution-info">
                <small>
                  Attribution ID: {msg.attributionId} |
                  Reward: ${msg.reward}
                </small>
              </div>
            )}
            <div className="timestamp">
              {new Date(msg.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message ai loading">
            <div className="typing-indicator">AI is typing...</div>
          </div>
        )}
      </div>

      <div className="input-container">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Ask the AI anything..."
          disabled={isLoading}
        />
        <button onClick={sendMessage} disabled={isLoading || !inputMessage.trim()}>
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatApp;
```

### Step 4: Styling

Create `src/components/ChatApp.css`:

```css
.chat-app {
  max-width: 800px;
  margin: 0 auto;
  height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 2px solid #e0e0e0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.rewards-display {
  display: flex;
  gap: 1rem;
  font-weight: bold;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  background: #f8f9fa;
}

.message {
  margin-bottom: 1rem;
  max-width: 70%;
}

.message.user {
  margin-left: auto;
}

.message.user .message-content {
  background: #007bff;
  color: white;
  padding: 0.75rem;
  border-radius: 18px 18px 4px 18px;
}

.message.ai .message-content {
  background: white;
  border: 1px solid #e0e0e0;
  padding: 0.75rem;
  border-radius: 18px 18px 18px 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.attribution-info {
  margin-top: 0.5rem;
  padding: 0.25rem 0.5rem;
  background: #e8f5e8;
  border-radius: 4px;
  font-size: 0.8rem;
  color: #2d5a2d;
}

.timestamp {
  font-size: 0.7rem;
  color: #666;
  margin-top: 0.25rem;
  text-align: right;
}

.input-container {
  display: flex;
  padding: 1rem;
  border-top: 1px solid #e0e0e0;
  background: white;
}

.input-container input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 20px;
  font-size: 1rem;
  outline: none;
}

.input-container input:focus {
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
}

.input-container button {
  margin-left: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

.input-container button:hover:not(:disabled) {
  background: #0056b3;
}

.input-container button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.typing-indicator {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  background: white;
  border-radius: 18px 18px 18px 4px;
  border: 1px solid #e0e0e0;
}

.loading .typing-indicator::after {
  content: '...';
  animation: typing 1.4s infinite;
}

@keyframes typing {
  0%, 60% { content: '...'; }
  30% { content: '..'; }
  90% { content: '.'; }
}
```

### Step 5: Environment Setup

Create `.env` in the backend folder:

```
UATP_API_KEY=your-uatp-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
```

Create `.env.local` in the React app root:

```
REACT_APP_UATP_API_KEY=your-uatp-api-key-here
```

### Step 6: Update App.js

Replace `src/App.js`:

```jsx
import React from 'react';
import ChatApp from './components/ChatApp';
import './App.css';

function App() {
  return (
    <div className="App">
      <ChatApp />
    </div>
  );
}

export default App;
```

### Step 7: Run the Application

```bash
# Terminal 1: Start backend
cd backend
npm start

# Terminal 2: Start frontend
cd ..
npm start
```

Visit `http://localhost:3000` and start chatting!

###  What You Built

- **Real-time chat** with AI responses
- **Attribution tracking** for every interaction
- **Economic rewards** displayed in real-time
- **User contribution** counting
- **Professional UI** with typing indicators

### Next Steps

- Add user authentication
- Implement message history persistence
- Add more AI platforms (Anthropic, HuggingFace)
- Create reward withdrawal functionality
- Add conversation analytics

---

## Tutorial 2: Economic Rewards System

**Time**: 30 minutes | **Level**: Beginner | **Stack**: Vue.js + Express

Build a comprehensive reward system that tracks user contributions and enables payouts.

### What You'll Build

- User dashboard with earnings overview
- Contribution history with attribution details
- Reward estimation for different content types
- Payout request functionality
- Leaderboard of top contributors

### Step 1: Backend Rewards API

```javascript
// backend/rewards-server.js
const express = require('express');
const { UATP } = require('@uatp/sdk');
require('dotenv').config();

const app = express();
const uatp = new UATP({ apiKey: process.env.UATP_API_KEY });

app.use(express.json());
app.use(require('cors')());

// Get user reward summary
app.get('/api/rewards/:userId', async (req, res) => {
  try {
    const rewards = await uatp.getAttributionRewards(req.params.userId);
    res.json(rewards);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get detailed reward history
app.get('/api/rewards/:userId/history', async (req, res) => {
  try {
    const { limit = 50, offset = 0 } = req.query;
    const history = await uatp.rewards.getRewardHistory(
      req.params.userId,
      { limit: parseInt(limit), offset: parseInt(offset) }
    );
    res.json(history);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Estimate content value
app.post('/api/estimate-value', async (req, res) => {
  try {
    const { contentType, contentSize, qualityScore } = req.body;
    const estimate = await uatp.estimateAttributionValue({
      contentType,
      contentSize,
      qualityScore
    });
    res.json(estimate);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Request payout
app.post('/api/rewards/:userId/payout', async (req, res) => {
  try {
    const { amount, paymentMethod, currency } = req.body;
    const result = await uatp.rewards.requestPayout({
      userId: req.params.userId,
      amount,
      paymentMethod,
      currency
    });
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get global economic metrics
app.get('/api/economics/global', async (req, res) => {
  try {
    const metrics = await uatp.getEconomicMetrics();
    res.json(metrics);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(3002, () => {
  console.log('Rewards server running on port 3002');
});
```

### Step 2: Vue.js Rewards Dashboard

```vue
<!-- src/components/RewardsDashboard.vue -->
<template>
  <div class="rewards-dashboard">
    <!-- Header with key metrics -->
    <div class="dashboard-header">
      <h1>Your Attribution Rewards</h1>
      <div class="metrics-grid">
        <div class="metric-card">
          <h3>${{ rewards.totalEarned || '0.00' }}</h3>
          <p>Total Earned</p>
        </div>
        <div class="metric-card">
          <h3>${{ rewards.pendingRewards || '0.00' }}</h3>
          <p>Pending</p>
        </div>
        <div class="metric-card">
          <h3>{{ rewards.attributionCount || 0 }}</h3>
          <p>Contributions</p>
        </div>
        <div class="metric-card">
          <h3>${{ monthlyProjection }}</h3>
          <p>Monthly Projection</p>
        </div>
      </div>
    </div>

    <!-- Tabs for different views -->
    <div class="tab-navigation">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="activeTab = tab.id"
        :class="{ active: activeTab === tab.id }"
        class="tab-button"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab Content -->
    <div class="tab-content">
      <!-- Overview Tab -->
      <div v-if="activeTab === 'overview'" class="overview-tab">
        <div class="section">
          <h3>Recent Activity</h3>
          <div class="activity-list">
            <div
              v-for="item in recentHistory.slice(0, 5)"
              :key="item.distributionId"
              class="activity-item"
            >
              <div class="activity-info">
                <strong>${{ item.amount }}</strong>
                <span>from {{ item.source }}</span>
              </div>
              <div class="activity-date">
                {{ formatDate(item.timestamp) }}
              </div>
            </div>
          </div>
        </div>

        <div class="section">
          <h3>Value Estimator</h3>
          <div class="estimator-form">
            <select v-model="estimator.contentType">
              <option value="text">Text Content</option>
              <option value="code">Code</option>
              <option value="image">Image</option>
              <option value="audio">Audio</option>
              <option value="video">Video</option>
            </select>
            <input
              v-model="estimator.contentSize"
              type="number"
              placeholder="Size (chars/bytes)"
            >
            <input
              v-model="estimator.qualityScore"
              type="number"
              step="0.1"
              min="0"
              max="1"
              placeholder="Quality (0-1)"
            >
            <button @click="estimateValue">Estimate</button>
          </div>
          <div v-if="valueEstimate" class="estimate-result">
            <p>Estimated Value: <strong>${{ valueEstimate.estimatedValue }}</strong></p>
            <p>Your Share: <strong>${{ valueEstimate.creatorReward }}</strong></p>
          </div>
        </div>
      </div>

      <!-- History Tab -->
      <div v-if="activeTab === 'history'" class="history-tab">
        <div class="history-controls">
          <input v-model="historyFilter" placeholder="Filter by source...">
          <select v-model="historySort">
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
            <option value="highest">Highest Amount</option>
            <option value="lowest">Lowest Amount</option>
          </select>
        </div>

        <div class="history-list">
          <div
            v-for="item in filteredHistory"
            :key="item.distributionId"
            class="history-item"
          >
            <div class="item-header">
              <span class="amount">${{ item.amount }}</span>
              <span class="source-badge" :class="item.source">{{ item.source }}</span>
            </div>
            <div class="item-details">
              <p>Distribution ID: {{ item.distributionId }}</p>
              <p v-if="item.attributionId">Attribution: {{ item.attributionId }}</p>
              <p>Status: <span :class="item.paymentStatus">{{ item.paymentStatus }}</span></p>
              <p>{{ formatDate(item.timestamp) }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Payouts Tab -->
      <div v-if="activeTab === 'payouts'" class="payouts-tab">
        <div class="payout-form">
          <h3>Request Payout</h3>
          <div class="form-group">
            <label>Amount</label>
            <input
              v-model="payout.amount"
              type="number"
              step="0.01"
              :max="availableForPayout"
              placeholder="Enter amount"
            >
            <small>Available: ${{ availableForPayout }}</small>
          </div>

          <div class="form-group">
            <label>Payment Method</label>
            <select v-model="payout.paymentMethod">
              <option value="bank_transfer">Bank Transfer</option>
              <option value="paypal">PayPal</option>
              <option value="crypto">Cryptocurrency</option>
              <option value="credits">Platform Credits</option>
            </select>
          </div>

          <div class="form-group">
            <label>Currency</label>
            <select v-model="payout.currency">
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
              <option value="BTC">Bitcoin</option>
              <option value="ETH">Ethereum</option>
            </select>
          </div>

          <button
            @click="requestPayout"
            :disabled="!canRequestPayout"
            class="payout-button"
          >
            Request Payout
          </button>
        </div>

        <div class="payout-info">
          <h4>Payout Information</h4>
          <ul>
            <li>Minimum payout: $10.00</li>
            <li>Processing time: 3-5 business days</li>
            <li>Transaction fee: 2.5%</li>
            <li>Payouts processed weekly</li>
          </ul>
        </div>
      </div>

      <!-- Analytics Tab -->
      <div v-if="activeTab === 'analytics'" class="analytics-tab">
        <div class="charts-container">
          <div class="chart-section">
            <h3>Earnings Over Time</h3>
            <canvas ref="earningsChart" width="400" height="200"></canvas>
          </div>

          <div class="stats-grid">
            <div class="stat-item">
              <h4>Average per Contribution</h4>
              <p>${{ averagePerContribution }}</p>
            </div>
            <div class="stat-item">
              <h4>Best Performing Content</h4>
              <p>{{ bestContentType }}</p>
            </div>
            <div class="stat-item">
              <h4>This Month's Growth</h4>
              <p>{{ monthlyGrowth }}%</p>
            </div>
            <div class="stat-item">
              <h4>Global Ranking</h4>
              <p>#{{ globalRank || 'N/A' }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'RewardsDashboard',
  props: {
    userId: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      activeTab: 'overview',
      rewards: {},
      recentHistory: [],
      fullHistory: [],
      valueEstimate: null,
      globalMetrics: {},

      tabs: [
        { id: 'overview', label: 'Overview' },
        { id: 'history', label: 'History' },
        { id: 'payouts', label: 'Payouts' },
        { id: 'analytics', label: 'Analytics' }
      ],

      estimator: {
        contentType: 'text',
        contentSize: 1000,
        qualityScore: 0.8
      },

      payout: {
        amount: '',
        paymentMethod: 'bank_transfer',
        currency: 'USD'
      },

      historyFilter: '',
      historySort: 'newest'
    };
  },

  computed: {
    monthlyProjection() {
      const currentEarnings = parseFloat(this.rewards.totalEarned || 0);
      const daysInMonth = 30;
      const today = new Date().getDate();
      const dailyAverage = currentEarnings / today;
      return (dailyAverage * daysInMonth).toFixed(2);
    },

    availableForPayout() {
      return this.rewards.pendingRewards || '0.00';
    },

    canRequestPayout() {
      const amount = parseFloat(this.payout.amount);
      const available = parseFloat(this.availableForPayout);
      return amount >= 10 && amount <= available;
    },

    filteredHistory() {
      let filtered = this.fullHistory.filter(item =>
        item.source.toLowerCase().includes(this.historyFilter.toLowerCase())
      );

      // Sort results
      switch (this.historySort) {
        case 'newest':
          filtered.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
          break;
        case 'oldest':
          filtered.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
          break;
        case 'highest':
          filtered.sort((a, b) => parseFloat(b.amount) - parseFloat(a.amount));
          break;
        case 'lowest':
          filtered.sort((a, b) => parseFloat(a.amount) - parseFloat(b.amount));
          break;
      }

      return filtered;
    },

    averagePerContribution() {
      const total = parseFloat(this.rewards.totalEarned || 0);
      const count = this.rewards.attributionCount || 1;
      return (total / count).toFixed(2);
    },

    bestContentType() {
      // Analyze history to find best performing content type
      const typeEarnings = {};
      this.fullHistory.forEach(item => {
        const type = item.metadata?.contentType || 'unknown';
        typeEarnings[type] = (typeEarnings[type] || 0) + parseFloat(item.amount);
      });

      let best = 'text';
      let maxEarnings = 0;
      for (const [type, earnings] of Object.entries(typeEarnings)) {
        if (earnings > maxEarnings) {
          maxEarnings = earnings;
          best = type;
        }
      }
      return best;
    },

    monthlyGrowth() {
      // Calculate month-over-month growth
      const now = new Date();
      const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1);

      const thisMonthEarnings = this.fullHistory
        .filter(item => new Date(item.timestamp) >= lastMonth)
        .reduce((sum, item) => sum + parseFloat(item.amount), 0);

      const previousMonthEarnings = this.fullHistory
        .filter(item => {
          const date = new Date(item.timestamp);
          return date >= new Date(now.getFullYear(), now.getMonth() - 2) &&
                 date < lastMonth;
        })
        .reduce((sum, item) => sum + parseFloat(item.amount), 0);

      if (previousMonthEarnings === 0) return '0';

      const growth = ((thisMonthEarnings - previousMonthEarnings) / previousMonthEarnings) * 100;
      return growth.toFixed(1);
    },

    globalRank() {
      // This would come from a leaderboard API
      return Math.floor(Math.random() * 10000) + 1;
    }
  },

  async mounted() {
    await this.loadRewards();
    await this.loadHistory();
    await this.loadGlobalMetrics();
  },

  methods: {
    async loadRewards() {
      try {
        const response = await axios.get(`/api/rewards/${this.userId}`);
        this.rewards = response.data;
      } catch (error) {
        console.error('Failed to load rewards:', error);
      }
    },

    async loadHistory() {
      try {
        const response = await axios.get(`/api/rewards/${this.userId}/history`);
        this.fullHistory = response.data;
        this.recentHistory = response.data.slice(0, 10);
      } catch (error) {
        console.error('Failed to load history:', error);
      }
    },

    async loadGlobalMetrics() {
      try {
        const response = await axios.get('/api/economics/global');
        this.globalMetrics = response.data;
      } catch (error) {
        console.error('Failed to load global metrics:', error);
      }
    },

    async estimateValue() {
      try {
        const response = await axios.post('/api/estimate-value', this.estimator);
        this.valueEstimate = response.data;
      } catch (error) {
        console.error('Failed to estimate value:', error);
      }
    },

    async requestPayout() {
      try {
        const response = await axios.post(`/api/rewards/${this.userId}/payout`, this.payout);
        if (response.data.success) {
          alert('Payout requested successfully!');
          this.payout.amount = '';
          await this.loadRewards(); // Refresh rewards
        } else {
          alert('Payout request failed: ' + response.data.error);
        }
      } catch (error) {
        console.error('Payout request failed:', error);
        alert('Payout request failed');
      }
    },

    formatDate(dateString) {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  }
};
</script>
```

###  Continue with More Tutorials

The tutorial series continues with:

- **Tutorial 3**: Governance Dashboard with voting
- **Tutorial 4**: Privacy-Preserving Analytics
- **Tutorial 5**: Content Creation Platform
- **Tutorial 6**: Watermarking Integration
- **Tutorial 7**: Democratic Voting System
- **Tutorial 8**: Cross-Platform Attribution

Each tutorial builds on the previous ones, creating a comprehensive understanding of UATP's capabilities.

---

##  Additional Resources

- **[Complete Code Examples](./examples/)** - Full source code for all tutorials
- **[API Reference](./api-reference.md)** - Detailed SDK documentation
- **[Best Practices](./best-practices.md)** - Production deployment guides
- **[Community Examples](./community/)** - Projects from other developers

**Ready to continue?** Pick your next tutorial or [join our Discord](https://discord.gg/uatp) to get help from the community!

---

*Building the future of attribution, one tutorial at a time*
