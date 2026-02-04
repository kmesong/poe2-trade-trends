# Learnings

- Frontend polling using `useEffect` and `setInterval` requires careful cleanup and state management to avoid race conditions or memory leaks.
- Mapping API data structures (snake_case) to UI component props (often camelCase) is a common pattern that should be handled explicitly.
- Influence calculation logic (comparing top vs bottom buckets) is effective for finding value drivers in item attributes.

# Patterns
- Polling pattern: Set `jobId` -> `useEffect` polls status -> `completed` -> fetch results -> clear `jobId`.
