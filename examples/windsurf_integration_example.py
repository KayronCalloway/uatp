#!/usr/bin/env python3
"""
Windsurf Integration Example
============================

This example shows how to integrate UATP capsule generation with Windsurf IDE
interactions for automatic attribution tracking.
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.live_capture.windsurf_hook import capture_windsurf_interaction


async def example_windsurf_integration():
    """Example of how to integrate UATP with Windsurf interactions."""

    print(" Windsurf UATP Integration Example")
    print("=" * 40)

    # Example 1: Code completion
    print("\n1. Code Completion Example")
    completion_capsule = await capture_windsurf_interaction(
        user_input="Create a TypeScript function to validate email addresses",
        assistant_response=r"""Here's a TypeScript function for email validation:

```typescript
export function validateEmail(email: string): boolean {
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

  // Basic format check
  if (!emailRegex.test(email)) {
    return false;
  }

  // Additional checks
  if (email.length > 320) { // RFC 5321 limit
    return false;
  }

  const [localPart, domain] = email.split('@');

  // Local part checks
  if (localPart.length > 64) { // RFC 5321 limit
    return false;
  }

  // Domain checks
  if (domain.length > 255) { // RFC 5321 limit
    return false;
  }

  return true;
}

// Usage example
const isValid = validateEmail("user@example.com");
console.log(isValid); // true
```

This function includes:
- RFC-compliant regex pattern
- Length validations
- Local part and domain checks
- TypeScript typing""",
        interaction_type="code_completion",
        file_context="src/utils/validation.ts",
        project_context="typescript-validation-utils",
        language="typescript",
        user_id="windsurf_developer",
    )

    if completion_capsule:
        print(f"[OK] Code completion capsule created: {completion_capsule}")

    # Example 2: Debugging help
    print("\n2. Debugging Session Example")
    debug_capsule = await capture_windsurf_interaction(
        user_input="Why is my async function not waiting for the Promise to resolve?",
        assistant_response="""This is a common async/await issue. Here are the most likely causes:

```javascript
// Problem: Missing await keyword
async function fetchData() {
  const result = fetch('/api/data'); // Missing await!
  return result.json(); // This will fail
}

// Solution: Add await
async function fetchData() {
  const result = await fetch('/api/data');
  return result.json();
}

// Problem: Not awaiting the function call
function handleClick() {
  fetchData(); // Missing await!
  console.log('Done'); // This runs before fetch completes
}

// Solution: Await the async function
async function handleClick() {
  await fetchData();
  console.log('Done'); // This runs after fetch completes
}
```

Common issues:
1. Forgetting `await` keyword
2. Not making the caller function `async`
3. Using `.then()` instead of `await`
4. Race conditions with multiple promises

Use `await` consistently and ensure your function is marked as `async`.""",
        interaction_type="debugging",
        file_context="src/api/dataService.js",
        language="javascript",
        error_context="Promise not resolving",
        user_id="windsurf_developer",
    )

    if debug_capsule:
        print(f"[OK] Debugging session capsule created: {debug_capsule}")

    # Example 3: Refactoring
    print("\n3. Refactoring Example")
    refactor_capsule = await capture_windsurf_interaction(
        user_input="Help me refactor this component to use React hooks instead of class components",
        assistant_response="""Here's how to refactor your class component to use React hooks:

```jsx
// Before: Class component
class UserProfile extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      user: null,
      loading: true,
      error: null
    };
  }

  async componentDidMount() {
    try {
      const user = await fetchUser(this.props.userId);
      this.setState({ user, loading: false });
    } catch (error) {
      this.setState({ error, loading: false });
    }
  }

  render() {
    const { user, loading, error } = this.state;
    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error.message}</div>;
    return <div>Hello, {user.name}!</div>;
  }
}

// After: Functional component with hooks
import { useState, useEffect } from 'react';

const UserProfile = ({ userId }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadUser = async () => {
      try {
        const userData = await fetchUser(userId);
        setUser(userData);
        setLoading(false);
      } catch (err) {
        setError(err);
        setLoading(false);
      }
    };

    loadUser();
  }, [userId]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  return <div>Hello, {user.name}!</div>;
};
```

Benefits of this refactoring:
- Simpler, more readable code
- Better performance with hooks
- Easier testing
- Modern React patterns""",
        interaction_type="refactoring",
        file_context="src/components/UserProfile.jsx",
        refactoring_type="class_to_hooks",
        language="javascript",
        user_id="windsurf_developer",
    )

    if refactor_capsule:
        print(f"[OK] Refactoring capsule created: {refactor_capsule}")

    # Example 4: Code explanation
    print("\n4. Code Explanation Example")
    explanation_capsule = await capture_windsurf_interaction(
        user_input="Can you explain how this regex pattern works?",
        assistant_response=r"""Let me break down this regex pattern for you:

```javascript
/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
```

**Pattern breakdown:**
- `^` - Start of string anchor
- `[a-zA-Z0-9._%+-]+` - Local part (before @)
  - `a-zA-Z0-9` - Letters and numbers
  - `._%+-` - Allowed special characters
  - `+` - One or more of the preceding characters
- `@` - Literal @ symbol
- `[a-zA-Z0-9.-]+` - Domain name part
  - `a-zA-Z0-9.-` - Letters, numbers, dots, hyphens
  - `+` - One or more characters
- `\.` - Literal dot (escaped)
- `[a-zA-Z]{2,}` - Top-level domain
  - `a-zA-Z` - Only letters
  - `{2,}` - At least 2 characters
- `$` - End of string anchor

**Examples it matches:**
- `user@example.com` [OK]
- `john.doe+tag@company.co.uk` [OK]
- `test123@sub.domain.org` [OK]

**Examples it rejects:**
- `user@domain` [ERROR] (no TLD)
- `@domain.com` [ERROR] (no local part)
- `user@` [ERROR] (no domain)

This pattern provides basic email validation but isn't 100% RFC-compliant.""",
        interaction_type="code_explanation",
        file_context="src/utils/validation.ts",
        code_context="email validation regex",
        language="javascript",
        user_id="windsurf_developer",
    )

    if explanation_capsule:
        print(f"[OK] Code explanation capsule created: {explanation_capsule}")

    print("\n All Windsurf integration examples completed!")
    print("   The system is now tracking Windsurf interactions automatically.")


if __name__ == "__main__":
    asyncio.run(example_windsurf_integration())
