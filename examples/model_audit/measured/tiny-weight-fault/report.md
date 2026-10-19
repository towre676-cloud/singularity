# Singularity deployment audit

**Result: CHANGED**

A flag means executed behavior differs from the reference beyond frozen clean tolerances; unchanged means no declared observation moved, not that the models are equivalent.

Package: `416178bd786e127c7cf490593c42e2ee3dbf8a4deaf01709be7e92ff98f47ccc`

Flagged probes: `[]`. Missing probes: `[]`. Identity/setting differences: `[{'key': 'checkpoint_provenance', 'declared': {'snapshot_manifest_sha256': '7ca592f567c635bb5da5538e2553cc7f98481a471b1030bb71275c5abf40920a'}, 'deployed': {'snapshot_manifest_sha256': 'f139a9ead2705578c185db976c39bb400becfaef8c5d4bc7eb0946558c97cc7b'}}]`.

Coverage is limited to the certificate's declared construction faults and frozen tolerances. A pass is not model equivalence, general quality, safety, or coverage of untested faults. Expected updates require a separately reviewed reference; CI never refreshes it automatically.

certificate.json contains the coverage witness; observations.json and report.json permit model-free replay. Hashes provide integrity, not authentication of research observations.
