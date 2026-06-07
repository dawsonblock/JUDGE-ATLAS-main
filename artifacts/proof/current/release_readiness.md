# RELEASE_READINESS

- generated_at_utc: 2026-06-07T09:24:31.228524+00:00
- overall_status: self-verifying-alpha
- alpha_candidate: true
- self_verifying_alpha: true
- production_release_candidate: false
- production_ready: false
- public_release_safe: false
- release_recommendation: self-verifying-alpha
- archive_hash: 131117bce06d46b2c73d436427a9f6477bfc7598
- platform: macOS-26.2-arm64-arm-64bit
- python_version: 3.11.9
- node_version: v22.22.3
- npm_version: 10.9.8

## Required Proof Gates

| gate | status | exit_code | log | sha256 |
|---|---|---:|---|---|
| check_no_pyc | PASS | 0 | artifacts/proof/current/check_no_pyc.log | a846f2e3cfab43e1b94af70247e6dff79ec62b983961a207185d87595b1b7ff6 |
| check_false_claims | PASS | 0 | artifacts/proof/current/check_false_claims.log | 8c882684eaade150d76d26e289c110f776b307c04d132c6aa33949aff87c7bc1 |
| check_source_keys | PASS | 0 | artifacts/proof/current/check_source_keys.log | 5a19cc9f9747d78ac73bb6e54323386b8a32b69079e204630f249748b6ffb39c |
| check_statuses | PASS | 0 | artifacts/proof/current/check_statuses.log | c5a1e374a12383ff2f924e70bd72bb2ba7210c803d1bba658765034a41a5b256 |
| check_no_direct_ingestion_network_clients | PASS | 0 | artifacts/proof/current/check_no_direct_ingestion_network_clients.log | 400d20f0847d3a353242d16e1bf3b80dce9fdfb219f416e162d1b7c8967fcafb |
| check_external_boundaries | PASS | 0 | artifacts/proof/current/check_external_boundaries.log | da039530a33bf730b0cc264637a3196b2212a42c42e24f50edcb6f1090c41b62 |
| check_dockerfile_copy_paths | PASS | 0 | artifacts/proof/current/check_dockerfile_copy_paths.log | 9cb5347afde90057ddc1a4fdcecd6ae1318290990ddadf2f5dfaeebf1e92eb2a |
| check_compose_auth_defaults | PASS | 0 | artifacts/proof/current/check_compose_auth_defaults.log | ce53c858a818dccbbd3685948e8ce1414dddb23714d77e259787b0ce79eceac9 |
| backend_compile | PASS | 0 | artifacts/proof/current/backend_compile.log | ff048fbcb05f4b23e858a813501477214166d826b765b8ca1f6bba526c2b6e9c |
| backend_import | PASS | 0 | artifacts/proof/current/backend_import.log | 6393cbd986957cbe5d40d4556853a5b1c49f25d6898cb7f61eaa8aee496ec4f5 |
| backend_pytest_collect | PASS | 0 | artifacts/proof/current/backend_pytest_collect.log | 9219ad7fbf0a03d91a1e243097cb1df9a12479b3e886d61b5eef4b48d9a06c4f |
| runtime_smoke | PASS | 0 | artifacts/proof/current/runtime_smoke.log | 561261d657b5b6b5bd99f9db4f716948b8a6188d16238c6259018c5ac421a7f3 |
| backend_pytest | PASS | 0 | artifacts/proof/current/backend_pytest.log | e7e92cd10c38363c73f75d61a407857c5a90af6a12bb1f727e9a0f81298f292f |
| check_migrations | PASS | 0 | artifacts/proof/current/check_migrations.log | b1a31ef1e482457fd1c47ac213cc98d199e78f8051acc81264a305cf629b66bf |
| docker_runtime_preflight | PASS | 0 | artifacts/proof/current/docker_runtime_preflight.log | ef3b6ef05510eb08e95145c029f77999cd4bfcc0dfe23bc6949a4012a210b597 |
| docker_smoke | PASS | 0 | artifacts/proof/current/docker_smoke.log | b0559df508aaa8bf97414c8242ddc580c08d58d8418a791204039e73bab4d27d |
| postgis_proof | PASS | 0 | artifacts/proof/current/postgis_proof.log | e7c2975870825a406517630681d0ea6a4ff5147cbde7dbdab1166587c223074b |
| egress_proxy_proof | PASS | 0 | artifacts/proof/current/egress_proxy_proof.log | f3c3885b372be1f7c5247175c5d482270fdcd9193822070dffae1d4f2e617c29 |
| demo_proof | PASS | 0 | artifacts/proof/current/demo_proof.log | 4b8de018d398c08e7e774fe218b49db64a69d06fa771256844a66194efff9655 |
| validate_sources | PASS | 0 | artifacts/proof/current/validate_sources.log | 3704f047a9579c5906775936cecc4b2bb34deafe905b85d73c69f63c2363b6a9 |
| check_yaml_duplicate_keys | PASS | 0 | artifacts/proof/current/check_yaml_duplicate_keys.log | 88b52b46f87e415fc01b849aececd79f567ac8ea21f09f1d891a37eca7ddb06d |
| verify_source_registry | PASS | 0 | artifacts/proof/current/verify_source_registry.log | 16cf7a8888bbb88a6527bd3081a7d8007b0f86efc5d443d3d5a7ba33a4e5c28c |
| source_registry_status | PASS | 0 | artifacts/proof/current/source_registry_status.log | de9e0de1944794266771043f45171dd1179979af2e0e408db8fed7b1f56802b8 |
| generate_coverage_matrix | PASS | 0 | artifacts/proof/current/generate_coverage_matrix.log | 3d868e3cbd1d339db9943afaaf81a5a2e3ad66fc852f8f7a5f57ffc063133f23 |
| check_source_registry_docs | PASS | 0 | artifacts/proof/current/check_source_registry_docs.log | 782dc5b673cedfeccea2aa35b3b38f215d1bfb4a0b2ad05ea0938bdd27214b34 |
| prepare_proof_db | PASS | 0 | artifacts/proof/current/prepare_proof_db.log | ef6779db88eeffa32551cb68ca12147f76837d1ef139b9e8d67f668940f260d5 |
| verify_evidence_store | PASS | 0 | artifacts/proof/current/verify_evidence_store.log | 7b693f37394b451d76dd236d9668d34a5e48b67f48dee151954763083deca20f |
| evidence_verification_standard | PASS | 0 | artifacts/proof/current/evidence_verification_standard.log | 135d21e9308aeca27d724d74b34077ea16cb290440c5de5a76e19c3b37604ee9 |
| evidence_verification_standard_pytest | PASS | 0 | artifacts/proof/current/evidence_verification_standard_pytest.log | c492c41580448240d0cd071f0c665f8548d9931c41518b75e86f2e55f4694f2a |
| source_registry_proof_pytest | PASS | 0 | artifacts/proof/current/source_registry_proof_pytest.log | 05e804a35468d0d64e8c4ba91441ea987473dd6736665b08b7b2b3be67644d93 |
| verify_audit_chain | PASS | 0 | artifacts/proof/current/verify_audit_chain.log | 94c410f5688c146534d3fac0ebde8ed28d76808fb105ef474f81fb845ffe87c8 |
| auth_mutation_route_coverage | PASS | 0 | artifacts/proof/current/auth_mutation_route_coverage.log | 4a64f86dcde28b25cf9f2a19086cd025d8bec3c035ea723832b7eb0ede98b354 |
| mutation_fail_closed_coverage | PASS | 0 | artifacts/proof/current/mutation_fail_closed_coverage.log | e2674b4dd23b51e181535802eb7f5ad73d380b9b414986ec2cc64dd3ef122708 |
| check_node_policy | PASS | 0 | artifacts/proof/current/check_node_policy.log | 20bc4a96240caa5415f01ad0cf2520f483d16aa14bf114ec9e251eab80bfdc4b |
| frontend_node_gate | PASS | 0 | artifacts/proof/current/frontend_node_gate.log | 39dc95fbc807439ae0edd07db104299b2a68d401fefe617df96cb835e3585dc9 |
| frontend_install | PASS | 0 | artifacts/proof/current/frontend_install.log | 451dae2de29ff70d27800de69c79b65b8406905de8d3d80482ab5bdecc721a2e |
| frontend_lint | PASS | 0 | artifacts/proof/current/frontend_lint.log | 9d79910829d5abcf1161f85f3d57cc9c745d1edd5734a88fee634c9913b368e8 |
| frontend_typecheck | PASS | 0 | artifacts/proof/current/frontend_typecheck.log | 701338e1389ab6284419cba533b353099f6b47658b930e128a8627a7a2d6d6e7 |
| frontend_contracts | PASS | 0 | artifacts/proof/current/frontend_contracts.log | 96f68c588255e4553c2391c6cc178de1098b04fc5e15df9e6a5eb0fdd3068ab2 |
| frontend_build | PASS | 0 | artifacts/proof/current/frontend_build.log | 39798d23c4446d3d60b08cb30d3115a9baeeeded0f0434dddee9a487463644b0 |
| check_api_contracts | PASS | 0 | artifacts/proof/current/check_api_contracts.log | f6750f8d64797a660c9122c245fa0ae38eb689dd8023b7fef1d0481e4ab86216 |
| frontend_backend_route_contract | PASS | 0 | artifacts/proof/current/frontend_backend_route_contract.log | f3563209ec0dcbcbf599836f73236926eee160235914e0fe0e660e945c9042a0 |
| frontend_route_smoke | PASS | 0 | artifacts/proof/current/frontend_route_smoke.log | 4afbcaf47374fb181a53b0939ce9ef84d5fde94e2028df8eb9e29b1fe9b322f0 |
| repo_generated_files | PASS | 0 | artifacts/proof/current/repo_generated_files.log | 1f136c767a6ec6bd6d527af249dd34271e19a2e1287eedd33fd8364bb9384137 |
| check_npm_audit_triage | PASS | 0 | artifacts/proof/current/check_npm_audit_triage.log | c9bab79018cc60539b4fa5a6d6b6e291f3138327e6689b409cb60d8087b54092 |
| map_route_check | PASS | 0 | artifacts/proof/current/map_route_check.log | 3f2c0fb18144134952224494bc6690cde35213914ff5880a8eed0b5ca519e30f |
| public_api_boundary | PASS | 0 | artifacts/proof/current/public_api_boundary.log | 968237b8f207fc28c12eb2aa64dbdefe7b7d81fd33058b980cdb6df656ebba08 |
| canlii_staging_proof | PASS | 0 | artifacts/proof/current/canlii_staging_proof.log | d7c9393bb589559678b644f26519944ef1a69f81a771fdbd5fce0282bb665ab5 |
| proof_freshness | PASS | 0 | artifacts/proof/current/proof_freshness.log | 2c919a043b67df4e99965039c70b960b4dea2651eb57c414347c0f8743bf11e6 |
| single_proof_authority | PASS | 0 | artifacts/proof/current/single_proof_authority.log | 67de9d9d555d8a633cccb3b3fd168f55f5975ed306de95965f06666949cc4337 |
| release_readiness_generation | PASS | 0 | artifacts/proof/current/release_readiness.md | 15b6ca5ab509117a4f45e817022e3a6283f2dd008ba18397a30e566b9d024635 |
| proof_consistency_pytest | PASS | 0 | artifacts/proof/current/proof_consistency_pytest.log | b62e3b569a79783d0c918701059e46ec7bd4aabbb4f2c6737a4f23b9e70350bf |
| archive_validation | PASS | 0 | artifacts/proof/current/archive_validation.log | 695a151f286e58be9c9a4b90591e52b5d0886e834584c802c9414c5a0ca2bfd7 |
| check_proof_manifest | PASS | 0 | artifacts/proof/current/check_proof_manifest.log | 652b5b93427a7011f67a82d8814c80478e93ba6e531ba15ca3bec2aa8a6d5b01 |
| check_no_local_paths_in_release_proof | PASS | 0 | artifacts/proof/current/check_no_local_paths_in_release_proof.log | 7ab4d071c63ecc123622b94a78dda4a32381a788cc2f318f840fe2f9e799c8e4 |
| check_proof_consistency | PASS | 0 | artifacts/proof/current/check_proof_consistency.log | 0a6ed516987c56172c896b5e5e4bae178cd6f9a2b53df2aa17bb118215f63a28 |
| required_proof_logs | PASS | 0 | artifacts/proof/current/required_proof_logs.log | fe0b1f0baf2755f5edae374bb5d2f57bade7a008916ce2e2c74a0ac951dadf61 |
| release_gate | PASS | 0 | artifacts/proof/current/release_gate.log | b85d39ed369032c3962fb7fa7c6cafb1f2ec57d95f6a8581f5e16660af3827bc |

## Optional Proof Gates

| gate | status | exit_code | log | sha256 |
|---|---|---:|---|---|
| static_guards | PASS | 0 | artifacts/proof/current/static_guards.log | 115a68267999528d3cc712acd354f443bc0db2bd743118066bb8d8f59c01ce65 |

## Remaining Blockers

- none

## Stale Or Misreported Claims

- none

## Next Repair Action

- Resolve any required failed gate and rerun scripts/release_gate.py.
