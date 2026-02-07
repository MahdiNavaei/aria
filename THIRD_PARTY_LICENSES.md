# Third-Party Licenses

This document lists all third-party open-source projects included in ARIA and their respective licenses.

---

## ⚠️ License Compatibility Warning

**IMPORTANT:** This project includes components with different licenses. Please review [LICENSE_COMPLIANCE.md](LICENSE_COMPLIANCE.md) for detailed information about license compatibility and legal obligations.

**Current Status:** ARIA (MIT) + AGPL v3 components = **LICENSE CONFLICT**

---

## Vendored Projects

### AGPL v3 Licensed Components

#### 1. AIHawk

```
GNU AFFERO GENERAL PUBLIC LICENSE
Version 3, 19 November 2007

Copyright (C) 2024 AI Hawk FOSS
```

- **Project:** Jobs Applier AI Agent (AIHawk)
- **Source:** https://github.com/feder-cr/Jobs_Applier_AI_Agent_AIHawk
- **Version:** Latest (see vendor/aihawk/UPSTREAM_VERSION.md)
- **License:** AGPL v3
- **License File:** [vendor/aihawk/LICENSE](vendor/aihawk/LICENSE)
- **Purpose:** LinkedIn and Indeed job application automation
- **Modifications:** Custom ARIA extensions in `aria_extensions/`

**License Summary:**
- ✅ You may use, modify, and distribute this software
- ⚠️ **You must disclose source code** when distributing
- ⚠️ **Network use triggers disclosure** (if users access over network, you must provide source)
- ⚠️ Modified versions must also be AGPL v3
- ⚠️ No warranty provided

**Full License:** https://www.gnu.org/licenses/agpl-3.0.en.html

---

#### 2. Skyvern

```
GNU AFFERO GENERAL PUBLIC LICENSE
Version 3, 19 November 2007

Copyright (C) 2007 Free Software Foundation, Inc.
```

- **Project:** Skyvern
- **Source:** https://github.com/Skyvern-AI/skyvern
- **Version:** v1.0.9 (see vendor/skyvern/UPSTREAM_VERSION.md)
- **License:** AGPL v3
- **License File:** [vendor/skyvern/LICENSE](vendor/skyvern/LICENSE)
- **Purpose:** Browser automation with vision-based form filling
- **Modifications:** Custom ARIA extensions in `aria_extensions/`

**License Summary:**
- ✅ You may use, modify, and distribute this software
- ⚠️ **You must disclose source code** when distributing
- ⚠️ **Network use triggers disclosure** (if users access over network, you must provide source)
- ⚠️ Modified versions must also be AGPL v3
- ⚠️ No warranty provided

**Full License:** https://www.gnu.org/licenses/agpl-3.0.en.html

---

### MIT Licensed Components

#### 3. browser-use

```
MIT License

Copyright (c) 2024 Gregor Zunic
```

- **Project:** browser-use
- **Source:** https://github.com/browser-use/browser-use
- **Version:** 0.5.2 (see vendor/browser-use/UPSTREAM_VERSION.md)
- **License:** MIT
- **License File:** [vendor/browser-use/LICENSE](vendor/browser-use/LICENSE)
- **Purpose:** AI-powered browser automation
- **Modifications:** Custom ARIA extensions in `aria_extensions/`

**License Summary:**
- ✅ You may use, modify, and distribute freely
- ✅ Commercial use allowed
- ✅ No disclosure requirements
- ✅ Can be used in proprietary software
- ⚠️ Must include copyright notice
- ⚠️ No warranty provided

**Full License:** https://opensource.org/licenses/MIT

---

#### 4. OpenAdapt

```
MIT License

Copyright (c) 2023 MLDSAI Inc., Richard Abrich, and contributors.
```

- **Project:** OpenAdapt
- **Source:** https://github.com/OpenAdaptAI/OpenAdapt
- **Version:** Latest (see vendor/openadapt/UPSTREAM_VERSION.md)
- **License:** MIT
- **License File:** [vendor/openadapt/LICENSE](vendor/openadapt/LICENSE)
- **Purpose:** Desktop automation with learn-by-demonstration
- **Modifications:** Custom ARIA extensions in `aria_extensions/`

**License Summary:**
- ✅ You may use, modify, and distribute freely
- ✅ Commercial use allowed
- ✅ No disclosure requirements
- ✅ Can be used in proprietary software
- ⚠️ Must include copyright notice
- ⚠️ No warranty provided

**Full License:** https://opensource.org/licenses/MIT

---

## Python Package Dependencies

ARIA also depends on numerous Python packages installed via pip/conda. Key licenses include:

### Core Dependencies

| Package | License | Purpose |
|---------|---------|---------|
| **LangChain** | MIT | LLM orchestration |
| **LangGraph** | MIT | Agent workflow graphs |
| **FastAPI** | MIT | REST API framework |
| **Streamlit** | Apache 2.0 | UI dashboard |
| **Playwright** | Apache 2.0 | Browser automation |
| **Redis** (client) | MIT | State storage client |
| **Qdrant** (client) | Apache 2.0 | Vector database client |
| **Pydantic** | MIT | Data validation |
| **PyAutoGUI** | BSD 3-Clause | Desktop automation |

For a complete list, see `pyproject.toml` or run:
```bash
pip-licenses --format=markdown
```

---

## Infrastructure Services

ARIA uses external services that have their own licenses:

| Service | License | Purpose |
|---------|---------|---------|
| **Redpanda** | BSL 1.1 (Business Source License) | Event streaming (Kafka-compatible) |
| **Redis** | BSD 3-Clause (or SSPL for newer versions) | State storage |
| **Qdrant** | Apache 2.0 | Vector database |
| **Ollama** | MIT | Local LLM runtime |

**Note:** These are typically run as separate Docker containers and do not affect ARIA's license directly, but users should be aware of their terms.

---

## License Compatibility Matrix

| Source License | ARIA MIT | Notes |
|----------------|----------|-------|
| MIT → MIT | ✅ Compatible | No restrictions |
| Apache 2.0 → MIT | ✅ Compatible | Must preserve Apache notices |
| BSD → MIT | ✅ Compatible | Must preserve BSD notices |
| **AGPL v3 → MIT** | ❌ **INCOMPATIBLE** | **Requires ARIA to be AGPL** |

---

## Compliance Requirements

### If You Use ARIA As-Is (with AGPL components)

**You MUST:**
1. ✅ Comply with AGPL v3 terms (disclose source code)
2. ✅ Provide source code to network users
3. ✅ License your modifications under AGPL v3
4. ✅ Include copyright notices from all dependencies

**You CANNOT:**
- ❌ Use ARIA in proprietary software without open-sourcing it
- ❌ Offer ARIA as a SaaS without publishing source code
- ❌ Claim ARIA is MIT-licensed (it's a combined AGPL work)

### If You Remove AGPL Components

**You MAY:**
1. ✅ Use ARIA under MIT license
2. ✅ Use in proprietary/commercial projects
3. ✅ No disclosure requirements

**But:**
- ⚠️ You lose AIHawk and Skyvern functionality
- ⚠️ Requires code refactoring

---

## Attribution Requirements

When using ARIA, you must include:

1. **This notice** in your distributions
2. **Copyright notices** from all dependencies
3. **License texts** from all dependencies

### Minimal Attribution

```
This software includes components from:
- browser-use (MIT) © 2024 Gregor Zunic
- OpenAdapt (MIT) © 2023 MLDSAI Inc., Richard Abrich, and contributors
- AIHawk (AGPL v3) © 2024 AI Hawk FOSS
- Skyvern (AGPL v3) © 2007 Free Software Foundation, Inc.

See THIRD_PARTY_LICENSES.md for full details.
```

---

## Updating Vendored Projects

When updating vendored projects:

1. Check for license changes in upstream
2. Update UPSTREAM_VERSION.md with new commit hash
3. Review new copyright holders
4. Update this file if licenses changed
5. Ensure ARIA extensions remain compatible

**Command:**
```bash
cd vendor/<project>
git fetch origin
git diff HEAD origin/main -- LICENSE
```

---

## Reporting License Issues

If you find a license issue:

1. **Check** [LICENSE_COMPLIANCE.md](LICENSE_COMPLIANCE.md) first
2. **Open an issue** at https://github.com/mahdinavaei/aria/issues
3. **Email** mahdinavaei1367@gmail.com for urgent matters

---

## Legal Disclaimer

**This document is provided for informational purposes only and does not constitute legal advice.**

- ARIA's authors are not responsible for license compliance of derivative works
- Users are responsible for ensuring their use complies with all applicable licenses
- Consult a qualified attorney for specific legal guidance

---

## Full License Texts

### AGPL v3

Full text: https://www.gnu.org/licenses/agpl-3.0.txt

Key excerpt (Section 13 - Remote Network Interaction):
> Notwithstanding any other provision of this License, if you modify the Program, your modified version must prominently offer all users interacting with it remotely through a computer network (if your version supports such interaction) an opportunity to receive the Corresponding Source of your version by providing access to the Corresponding Source from a network server at no charge...

### MIT License

Full text: https://opensource.org/licenses/MIT

```
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

## Additional Resources

- [Choose a License](https://choosealicense.com/)
- [SPDX License List](https://spdx.org/licenses/)
- [GNU License Compatibility](https://www.gnu.org/licenses/license-list.html)
- [OSI Approved Licenses](https://opensource.org/licenses)

---

<div align="center">

**For questions about licensing, see [LICENSE_COMPLIANCE.md](LICENSE_COMPLIANCE.md)**

*Last Updated: February 7, 2026*

</div>
