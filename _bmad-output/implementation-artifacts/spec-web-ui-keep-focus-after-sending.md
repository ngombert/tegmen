---
title: 'Keep focus on chat input field after sending a message'
type: 'feature'
created: '2026-06-23T22:26:01+02:00'
status: 'done'
route: 'one-shot'
---

# Keep focus on chat input field after sending a message

## Intent

**Problem:** When a user sends a message in the web UI, the input field gets disabled during loading and subsequently loses focus, requiring the user to click the input field again to type the next message.

**Approach:** Add an `inputRef` to the input element and implement a React `useEffect` hook that detects when `isLoading` transitions from `true` to `false` to focus the input field again, while ensuring we do not hijack focus on initial mount or yank focus from other active elements.

## Suggested Review Order

**UI Focus Management**

- Added inputRef to store reference to the input DOM node
  [ChatLayout.tsx:13](../../src/web-client/src/components/ChatLayout.tsx#L13)

- Auto-focus input when message finishes sending (isLoading becomes false) without hijacking initial mount focus
  [ChatLayout.tsx:22](../../src/web-client/src/components/ChatLayout.tsx#L22)

- Bind the inputRef reference to the input element
  [ChatLayout.tsx:89](../../src/web-client/src/components/ChatLayout.tsx#L89)
