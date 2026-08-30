# Printer Troubleshooting Guide

## Common Issue: Printer Not Showing Up / Cannot Connect

**Troubleshooting Steps:**
1. Confirm the employee is connected to the office Wi-Fi or wired network (printers are not accessible remotely/via VPN).
2. Check the printer itself is powered on and displaying a ready status on its screen.
3. On the employee's computer, remove the printer from the printer list and re-add it via the company's Printer Setup tool (available on the IT intranet page).
4. Restart the print spooler service (Windows: services.msc > Print Spooler > Restart).
5. If the printer does not appear in the network printer list at all, it may be offline at the hardware level — escalate for a physical check.

## Common Issue: Print Jobs Stuck in Queue

**Troubleshooting Steps:**
1. Open the print queue and cancel all pending jobs.
2. Restart the print spooler service.
3. Try printing a small test document (single page) to confirm the queue is now clear.
4. If jobs continue to get stuck after clearing and restarting, this may indicate a driver issue and should be escalated.

## Common Issue: Poor Print Quality (Streaks, Faded Text)

**Troubleshooting Steps:**
1. This is typically a hardware/consumables issue, not something resolvable remotely.
2. Check with office facilities whether toner/ink was recently replaced.
3. If this is a shared office printer, escalate directly — physical maintenance is required, not IT software troubleshooting.
