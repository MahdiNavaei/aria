# License Compliance Report

**Project:** ARIA (Adaptive Reasoning & Intelligent Automation)  
**Date:** February 7, 2026  
**Status:** ⚠️ **LICENSE CONFLICT DETECTED - ACTION REQUIRED**

---

## Executive Summary

ARIA currently contains a **critical license incompatibility** that requires immediate attention. The project uses the permissive MIT License, but includes vendored dependencies licensed under the restrictive AGPL v3, creating a legal conflict.

### Key Finding

**❌ License Conflict:** ARIA (MIT) includes AGPL v3 code (AIHawk, Skyvern), which is legally incompatible for network services.

---

## Detailed License Analysis

### ARIA Core License

```
MIT License
Copyright (c) 2026 ARIA

✅ Permissive license allowing:
- Commercial use
- Modification
- Distribution
- Private use
- Sublicensing
```

### Vendor Dependencies Analysis

| Dependency | License | Compatible with MIT? | Risk Level | Action Required |
|------------|---------|---------------------|------------|-----------------|
| **browser-use** | MIT | ✅ Yes | ✅ None | None |
| **OpenAdapt** | MIT | ✅ Yes | ✅ None | None |
| **AIHawk** | **AGPL v3** | ❌ **No** | 🔴 **Critical** | **Yes** |
| **Skyvern** | **AGPL v3** | ❌ **No** | 🔴 **Critical** | **Yes** |

---

## AGPL v3 License Requirements

### What is AGPL v3?

The GNU Affero General Public License v3 is a "strong copyleft" license with special network provisions:

#### Key Provisions:

1. **Section 13 - Remote Network Interaction:**
   > "If you modify the Program, your modified version must prominently offer all users interacting with it remotely through a computer network an opportunity to receive the Corresponding Source."

2. **Copyleft Effect:**
   - Any software that incorporates AGPL code must also be AGPL
   - This includes libraries, plugins, and integrated components
   - The "viral" nature extends to the entire combined work

3. **Network Service Clause:**
   - Unlike GPL, AGPL covers network services (SaaS, APIs, web apps)
   - Users interacting over a network must have access to source code
   - This closes the "ASP loophole" present in GPL

### How This Affects ARIA

Since ARIA:
- Includes AGPL v3 code in `vendor/aihawk/` and `vendor/skyvern/`
- Operates as a network service (FastAPI, WebSocket)
- Modifies and extends the vendored libraries

**Legal Requirement:**
- ARIA must either comply with AGPL v3 terms (release all source code under AGPL)
- OR remove the AGPL dependencies entirely
- OR isolate them in a way that avoids creating a "combined work"

---

## Legal Risks

### Current Situation

**Risk Assessment: 🔴 HIGH**

1. **License Violation:**
   - Distributing ARIA with AGPL code under MIT license is a license violation
   - Recipients may unknowingly violate AGPL terms

2. **Enforcement:**
   - AGPL copyright holders can enforce compliance
   - Potential for takedown notices or legal action

3. **User Liability:**
   - Users deploying ARIA as a service may unknowingly violate AGPL
   - They could face legal consequences

4. **Commercial Use:**
   - Companies cannot use ARIA in proprietary products without open-sourcing everything
   - This severely limits adoption

### Not Compliant Scenarios

❌ **You CANNOT:**
- Distribute ARIA as MIT while including AGPL dependencies
- Offer ARIA as a SaaS without publishing full source code
- Use ARIA in proprietary software without making it AGPL
- Claim MIT license while incorporating AGPL components

---

## Recommended Solutions

### Option 1: Change ARIA License to AGPL v3 ✅ **RECOMMENDED**

**Description:**
Change the entire ARIA project license from MIT to AGPL v3 to match the vendored dependencies.

**Implementation:**
```bash
# Update LICENSE file
# Update all file headers
# Update documentation
# Notify users of license change
```

**Pros:**
- ✅ Full legal compliance with vendor licenses
- ✅ Aligns with open-source philosophy
- ✅ No code changes required
- ✅ Users know exactly what they're getting
- ✅ Encourages community contributions

**Cons:**
- ❌ Restricts commercial closed-source use
- ❌ May reduce adoption by companies
- ❌ Network service users must open-source modifications
- ❌ Cannot be relicensed easily in the future

**Impact:**
- Users must comply with AGPL v3 terms
- Anyone offering ARIA as a service must publish source code
- Encourages a vibrant open-source ecosystem

**Verdict:** 🟢 **Best for open-source projects prioritizing community over commercial adoption**

---

### Option 2: Remove AGPL Dependencies (AIHawk, Skyvern)

**Description:**
Remove `vendor/aihawk/` and `vendor/skyvern/` entirely from the project.

**Implementation:**
```bash
# Remove directories
rm -rf vendor/aihawk vendor/skyvern

# Refactor code to remove dependencies
# Implement alternative solutions or plugins
# Update documentation
```

**Pros:**
- ✅ Maintains MIT license
- ✅ Maximum flexibility for users
- ✅ No legal conflicts
- ✅ Can be used in proprietary software

**Cons:**
- ❌ Loses functionality from these libraries
- ❌ Requires significant refactoring
- ❌ May need to reimplement features
- ❌ Reduces ARIA's capabilities

**Impact:**
- ARIA remains MIT but loses job application features
- Need alternative implementations for LinkedIn/Indeed automation
- Skyvern form-filling capabilities lost

**Verdict:** 🟡 **Best for commercial-friendly projects willing to sacrifice features**

---

### Option 3: Dual Licensing with Optional AGPL Plugins

**Description:**
Keep ARIA core as MIT, but isolate AGPL dependencies as optional, separately-licensed plugins.

**Architecture:**
```
aria/               (MIT License)
├── src/aria/      (Core MIT code)
├── plugins/       (Plugin system)
└── LICENSE        (MIT)

aria-agpl-plugins/ (Separate repository, AGPL License)
├── aihawk/        (AGPL)
├── skyvern/       (AGPL)
└── LICENSE        (AGPL v3)
```

**Implementation:**
1. Create a plugin system with clean interfaces
2. Move AIHawk and Skyvern to separate repository
3. Document installation: `pip install aria aria-agpl-plugins`
4. Clear licensing documentation

**Pros:**
- ✅ Core ARIA remains MIT (maximum flexibility)
- ✅ Users can choose to add AGPL features
- ✅ Clear separation of licenses
- ✅ Both ecosystems can coexist

**Cons:**
- ❌ Significant architectural refactoring required
- ❌ Complex dependency management
- ❌ Users may be confused about licensing
- ❌ Plugin boundaries must be very clean (no tight coupling)

**Legal Risk:**
- ⚠️ If plugins are too tightly integrated, could still be considered "combined work"
- ⚠️ Requires careful legal review of plugin architecture

**Verdict:** 🟡 **Best for large projects with resources for refactoring**

---

### Option 4: Use Dynamic Linking / Plugin Interfaces

**Description:**
Implement AGPL dependencies as separate processes that communicate via APIs, avoiding "combined work" classification.

**Architecture:**
```
ARIA Core (MIT)
    ↕️ (REST API / IPC)
AIHawk Service (AGPL) - separate process
    ↕️ (REST API / IPC)
Skyvern Service (AGPL) - separate process
```

**Implementation:**
- Run AGPL components as separate Docker containers
- Communicate via REST APIs or message queues
- No direct code linking or imports

**Pros:**
- ✅ Clearer license separation
- ✅ Core ARIA remains MIT
- ✅ AGPL components isolated

**Cons:**
- ❌ Legal gray area (could still be "combined work")
- ❌ Performance overhead
- ❌ Complexity in deployment
- ❌ Not universally accepted as AGPL-compliant

**Legal Risk:**
- ⚠️ Courts may still view this as a single combined work
- ⚠️ AGPL authors may disagree with this interpretation

**Verdict:** 🔴 **Risky - Not recommended without legal counsel**

---

## Compliance Checklist

To achieve full license compliance, complete these steps:

### Immediate Actions (This Week)

- [ ] **Choose a solution** from the options above
- [ ] **Create THIRD_PARTY_LICENSES.md** listing all dependencies
- [ ] **Add license notices** to README
- [ ] **Notify users** via GitHub release notes

### Short-term Actions (This Month)

#### If choosing Option 1 (AGPL):
- [ ] Update LICENSE file to AGPL v3
- [ ] Add AGPL headers to all source files
- [ ] Update README badges and documentation
- [ ] Publish announcement about license change

#### If choosing Option 2 (Remove AGPL):
- [ ] Remove vendor/aihawk and vendor/skyvern
- [ ] Refactor code to remove dependencies
- [ ] Implement alternative solutions
- [ ] Test thoroughly

#### If choosing Option 3 (Plugins):
- [ ] Design plugin architecture
- [ ] Create separate repository for AGPL plugins
- [ ] Refactor code to use plugin system
- [ ] Update documentation

### Long-term Actions

- [ ] **Legal review** by a lawyer familiar with open-source licensing
- [ ] **Contributor License Agreement (CLA)** if accepting external contributions
- [ ] **Regular audits** of new dependencies
- [ ] **Automated license checking** in CI/CD pipeline

---

## THIRD_PARTY_LICENSES.md (Required)

Create a file listing all vendored projects:

```markdown
# Third-Party Licenses

## AGPL v3 Licensed Components

### AIHawk
- **License:** GNU Affero General Public License v3
- **Source:** https://github.com/feder-cr/Jobs_Applier_AI_Agent_AIHawk
- **Copyright:** © 2024 AI Hawk FOSS
- **Full License:** See vendor/aihawk/LICENSE

### Skyvern
- **License:** GNU Affero General Public License v3
- **Source:** https://github.com/Skyvern-AI/skyvern
- **Copyright:** © 2007 Free Software Foundation, Inc.
- **Full License:** See vendor/skyvern/LICENSE

## MIT Licensed Components

### browser-use
- **License:** MIT License
- **Source:** https://github.com/browser-use/browser-use
- **Copyright:** © 2024 Gregor Zunic
- **Full License:** See vendor/browser-use/LICENSE

### OpenAdapt
- **License:** MIT License
- **Source:** https://github.com/OpenAdaptAI/OpenAdapt
- **Copyright:** © 2023 MLDSAI Inc., Richard Abrich, and contributors
- **Full License:** See vendor/openadapt/LICENSE
```

---

## Recommended Action Plan

### Step 1: Immediate Decision (Next 48 Hours)

**Choose one:**
1. ✅ **Accept AGPL** - Change ARIA to AGPL v3 (RECOMMENDED for open-source projects)
2. 🟡 **Remove AGPL** - Keep MIT, sacrifice features
3. 🟡 **Refactor** - Plugin architecture (if you have time/resources)

### Step 2: Implementation (Next 2 Weeks)

Follow the compliance checklist for your chosen option.

### Step 3: Communication (Next 1 Week)

- Update README with licensing information
- Notify existing users
- Update documentation
- Create release notes

### Step 4: Legal Review (Within 1 Month)

Consult with a lawyer to ensure full compliance.

---

## Questions & Answers

### Q: Can I just keep both licenses and let users choose?

**A:** ❌ No. Dual licensing requires explicit permission from all copyright holders. You cannot unilaterally dual-license AGPL code.

### Q: What if I don't deploy ARIA as a network service?

**A:** ⚠️ AGPL still applies to distribution. Anyone who receives ARIA can deploy it as a service, triggering AGPL obligations.

### Q: Can I use AIHawk/Skyvern internally without releasing source?

**A:** ⚠️ Section 13 of AGPL triggers on network interaction. If users access it over a network, you must provide source code.

### Q: What about Fair Use?

**A:** ❌ Software licenses are contracts, not copyright claims. Fair use doesn't apply to license violations.

### Q: Can I claim this is educational/research use?

**A:** ❌ AGPL applies regardless of purpose (commercial, educational, personal).

---

## External Resources

### License Texts
- [MIT License](https://opensource.org/licenses/MIT)
- [AGPL v3 License](https://www.gnu.org/licenses/agpl-3.0.en.html)
- [GPL Compatibility Matrix](https://www.gnu.org/licenses/gpl-faq.html#AllCompatibility)

### License Guides
- [Choose a License](https://choosealicense.com/)
- [TLDRLegal - AGPL v3](https://www.tldrlegal.com/license/gnu-affero-general-public-license-v3-agpl-3-0)
- [GitHub Licensing Guide](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)
- [AGPL Explained](https://www.gnu.org/licenses/why-affero-gpl.html)

### Legal Advice
- [Software Freedom Law Center](https://softwarefreedom.org/)
- [Open Source Initiative](https://opensource.org/licenses)

**⚠️ Disclaimer:** This document provides general information, not legal advice. Consult a qualified attorney for specific guidance.

---

## Contact

For questions about this compliance report:
- **Email:** mahdinavaei1367@gmail.com
- **GitHub Issues:** [ARIA Repository](https://github.com/mahdinavaei/aria/issues)

---

<div align="center">

**Status:** 🔴 **NON-COMPLIANT - ACTION REQUIRED**

*Last Updated: February 7, 2026*

</div>
