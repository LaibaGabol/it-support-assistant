# Email & Outlook Issues

## Common Issue: Not Receiving Emails

**Troubleshooting Steps:**
1. Check the Junk/Spam folder first — a large share of "missing" emails are misfiled by spam filters.
2. Confirm the mailbox is not full (Outlook > Account Settings > Mailbox Usage). Full mailboxes silently reject new mail.
3. Check whether the sender's domain may be on the company's blocklist — ask the employee for the sender's email domain.
4. Confirm Outlook is properly synced (File > Account Settings > check "Connected" status, not "Disconnected" or "Needs Attention").
5. If none of the above resolves it and mail is confirmed missing (not just delayed), escalate for a mail flow/transport log check — this requires backend access IT does not have via self-service tools.

## Common Issue: Cannot Send Emails

**Troubleshooting Steps:**
1. Check for a bounce-back error message and read its content — it usually indicates the specific cause (mailbox full, invalid recipient, size limit exceeded).
2. Confirm attachment size is under 25MB (company limit); larger files should be shared via the company file-sharing tool instead.
3. Restart Outlook fully (not just minimize).
4. If sending fails with no bounce-back and no clear error, escalate — this may indicate an authentication or relay issue.

## Common Issue: Outlook Running Very Slowly

**Troubleshooting Steps:**
1. Check mailbox size — mailboxes over 5GB commonly cause performance issues in desktop Outlook.
2. Disable unnecessary add-ins (File > Options > Add-ins > Manage: COM Add-ins).
3. Run Outlook in Safe Mode to test if an add-in is the cause.
4. If slowness persists in Safe Mode with no add-ins active, escalate for further investigation.
