# VPN Troubleshooting Guide

## Common Issue: VPN Disconnects Frequently

**Symptoms:** VPN connection drops every few minutes, requires frequent reconnection.

**Troubleshooting Steps:**
1. Confirm the employee is using the official company VPN client (GlobalProtect), not a personal or third-party VPN app.
2. Restart the VPN client application (not just reconnect — fully quit and relaunch).
3. Restart the computer, as background updates or stale network adapters can interrupt VPN sessions.
4. Check Wi-Fi signal strength — VPN drops are common on weak or congested Wi-Fi. Recommend switching to a wired connection if available.
5. Confirm the VPN client is on the latest version (Settings > About in the client).
6. If the issue persists after all steps above, this likely requires escalation — frequent disconnects with no clear cause often indicate a server-side or network configuration issue that IT needs to investigate directly.

## Common Issue: Cannot Connect to VPN At All

**Symptoms:** VPN client shows "connection failed" or times out on connect.

**Troubleshooting Steps:**
1. Verify internet connectivity is working outside the VPN (can the user browse normal websites?).
2. Confirm username and password are correct and the account is not locked (see Password Reset guide).
3. Check if multi-factor authentication (MFA) push notification was approved on the employee's phone.
4. Restart the VPN client and computer.
5. If the VPN server itself may be down, check the IT status page. If down for the employee only (not company-wide), escalate.

## Common Issue: Slow Speeds While Connected to VPN

**Symptoms:** Internet or internal tools are noticeably slower once VPN is active.

**Troubleshooting Steps:**
1. This is often expected behavior, since all traffic routes through the VPN server. Confirm the slowdown is significantly worse than normal (not just mildly slower).
2. Try switching VPN server region if the client allows manual region selection — connecting to a geographically closer server often helps.
3. If speeds are unusable for work, escalate with details on which sites/tools are affected.
