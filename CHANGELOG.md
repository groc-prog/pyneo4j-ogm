# CHANGELOG




## What's Changed in v0.5.2 (2024-02-22)




### Documentation


* docs: add docs for migrations ([`c94ce30`](https://github.com/groc-prog/pyneo4j-ogm/commit/c94ce304445fe2ed49bb8d8640bfe2a1eb1fbc8f))


### Refactor


* refactor: remove tabulate and add pretty_print function ([`9f29344`](https://github.com/groc-prog/pyneo4j-ogm/commit/9f29344d316e67d2cc609b289a01160adec316ff))


## What's Changed in v0.5.1 (2024-02-11)



### Documentation


* docs: update docs ([`98ff03c`](https://github.com/groc-prog/pyneo4j-ogm/commit/98ff03c81ff1130b41d163242fd68d830c17785c))


### Fix


* fix: fix validation error when passing &#34;*&#34; to $maxHops ([`960aa76`](https://github.com/groc-prog/pyneo4j-ogm/commit/960aa76148f782089d522826052aa491dc8f0072))


* fix: fix validation error when passing &#34;*&#34; to $maxHops ([`753af19`](https://github.com/groc-prog/pyneo4j-ogm/commit/753af193a60042559d3be0e67471dddb4f66544a))

## What's Changed in v0.5.0 (2024-02-06)




### Documentation


* docs: update documentation ([`87b21af`](https://github.com/groc-prog/pyneo4j-ogm/commit/87b21af4232e916a716b5336e24e5791db0fb75c))


* docs: update docs ([`892e67d`](https://github.com/groc-prog/pyneo4j-ogm/commit/892e67d9fbe2291b5464afcafb82f3ee6094a841))


* docs: update docs ([`ee5fced`](https://github.com/groc-prog/pyneo4j-ogm/commit/ee5fcedaf1be408db0b025ed6d4bd0888c549c1d))


### Feature


* feat: add down command ([`593dcc5`](https://github.com/groc-prog/pyneo4j-ogm/commit/593dcc5789e29505708dd460d5d1eaeec574b87f))


* feat: add up action in cli ([`102df70`](https://github.com/groc-prog/pyneo4j-ogm/commit/102df70db6f743df9bdde51eccf99454a27e1210))


* feat: status command for displaying state of migrations ([`4e4ba14`](https://github.com/groc-prog/pyneo4j-ogm/commit/4e4ba14d3ea95d17142767419c021837776bfd86))


* feat: add support for storage of deeply nested lists ([`1b5afc9`](https://github.com/groc-prog/pyneo4j-ogm/commit/1b5afc925f71439eb1e9e216d7aa55652e455aeb))


### Fix


* fix: correctly pass arguments ([`9d1fce5`](https://github.com/groc-prog/pyneo4j-ogm/commit/9d1fce5e57821cbbec52f2eea87c8a4a5f69f55f))


* fix: return created file name and path from create action ([`3965d23`](https://github.com/groc-prog/pyneo4j-ogm/commit/3965d2300470360fdcba1392dc7dacafc92bb4ee))


* fix: add missing __init__ file for migrations ([`f1e196b`](https://github.com/groc-prog/pyneo4j-ogm/commit/f1e196bf017998677fd5a5531e0fb37885ec63c5))


* fix: add start/end node element_id/id to relationship serialization ([`986ebc6`](https://github.com/groc-prog/pyneo4j-ogm/commit/986ebc65a676579ffdfa784866cf4892a782b84a))


* fix: rename _inflate parameter, fix element_id and id being included in modified_properties ([`e1672bd`](https://github.com/groc-prog/pyneo4j-ogm/commit/e1672bd88aa585aa4c32faf3a35593f4c184ab4f))


* fix: fix exception when using polymorphism with node models ([`54e266d`](https://github.com/groc-prog/pyneo4j-ogm/commit/54e266d8553c0083a19bc9af9914b329236602fc))


* fix: fix inherited node model labels ([`c49186c`](https://github.com/groc-prog/pyneo4j-ogm/commit/c49186cbe222cb3fc357073e8fc10e05e67bcee0))


* fix: fix node model labels when inheriting from another model ([`4d64c65`](https://github.com/groc-prog/pyneo4j-ogm/commit/4d64c65ee8bc1eca8999e70268fb610ef2436888))


* fix: correctly inherit settings from parent class ([`9f94f0c`](https://github.com/groc-prog/pyneo4j-ogm/commit/9f94f0c58f919d06ec06f074e74a1e68c943356f))


* fix: fix __iter__ method ([`f945a17`](https://github.com/groc-prog/pyneo4j-ogm/commit/f945a17103ce1123347ea7f118dac7b0c5e7c162))


* fix: use new relationship property instance instead of mutating the base class ([`2d084d9`](https://github.com/groc-prog/pyneo4j-ogm/commit/2d084d96409d7970e56039e3e59495c859502a53))


* fix: check if node needs to be parsed before doing so ([`a867228`](https://github.com/groc-prog/pyneo4j-ogm/commit/a86722839adfa276cd3071dfd0f23545cf4ef5ac))


* fix: parsing exported models now also parses relationship property nodes to their models ([`28c5efe`](https://github.com/groc-prog/pyneo4j-ogm/commit/28c5efe2e0697a6b787fe08fba4b5e4bfefacd5c))


* fix: remove unnecessary coroutine check ([`2e176a0`](https://github.com/groc-prog/pyneo4j-ogm/commit/2e176a085c861d80fb9d9c320e737daf062ac02f))


* fix: make auto_fetch_nodes optional ([`3d1917c`](https://github.com/groc-prog/pyneo4j-ogm/commit/3d1917c2c7a67eba1258678b5821e8a88f04a203))


* fix: correctly parse dict to model when model defines RelationshipProperty field ([`9766204`](https://github.com/groc-prog/pyneo4j-ogm/commit/9766204a19d3cf70bc1c9812588d9c11a1ad716b))


* fix: fix index/constraint schema ([`cb4eeb7`](https://github.com/groc-prog/pyneo4j-ogm/commit/cb4eeb7fe97bfd5ed5b2b046816bb408846ada4a))


### Refactor


* refactor: rename applied_at to updated_at ([`63d585c`](https://github.com/groc-prog/pyneo4j-ogm/commit/63d585c3be3a7069c2fe7e0dec9120153b667150))


* refactor: refactor way auth info is passed in config ([`5ab25f0`](https://github.com/groc-prog/pyneo4j-ogm/commit/5ab25f0b8790857d8a4cbd12409a23aecc8da90d))


* refactor: move defaults to separate file, actions now accept arguments instead of namespace ([`fe59988`](https://github.com/groc-prog/pyneo4j-ogm/commit/fe59988dddc60f1f1f500aa7ec11ece2a1b6e1b0))


* refactor: rename inner decorator function ([`16bc5b8`](https://github.com/groc-prog/pyneo4j-ogm/commit/16bc5b8d911674a9ae1a0fd9fc2d9f2c866cfd89))


* refactor: move relationship property enums to relationship property file ([`47e0b6b`](https://github.com/groc-prog/pyneo4j-ogm/commit/47e0b6b7a9b2a8ea52b133b65cb9eda37d929c6c))


* refactor: remove unnecessary if statements ([`f6f7bfe`](https://github.com/groc-prog/pyneo4j-ogm/commit/f6f7bfee206ea41158e40946eafa0e21518a3307))


* refactor: adjust used logging level ([`e835c7a`](https://github.com/groc-prog/pyneo4j-ogm/commit/e835c7a45410c3df13e9b2eb3940df35eb25ee81))


* refactor: change file structure and move enums/types/consts ([`a6851a2`](https://github.com/groc-prog/pyneo4j-ogm/commit/a6851a2ea7dc0b8dfda53270c8e795c194d72476))



## What's Changed in v0.4.1 (2024-01-17)




### Documentation


* docs: update docs on serialization ([`03d740f`](https://github.com/groc-prog/pyneo4j-ogm/commit/03d740f71a7a4cb48c61e3fc57933b2867a367d4))


* docs: update docs on running test suite ([`0a9c914`](https://github.com/groc-prog/pyneo4j-ogm/commit/0a9c914e04e4b5b1fc58d23d0042702f67b2d538))


* docs: add docs for pydantic version and supported features ([`99546ca`](https://github.com/groc-prog/pyneo4j-ogm/commit/99546cace3d0a184c52b8b7620f96ca719dae22f))


* docs: add docs for running test suits ([`f24f62c`](https://github.com/groc-prog/pyneo4j-ogm/commit/f24f62cec2f8f4862b9c0beab6b57d09f4b4f9e4))


* docs: fix format issues for tables ([`1f0fa1e`](https://github.com/groc-prog/pyneo4j-ogm/commit/1f0fa1e6aac0601c5a742a65c27696248c49c151))


* docs: add supported pydantic versions ([`5f3c637`](https://github.com/groc-prog/pyneo4j-ogm/commit/5f3c637c740bd7caab3d6f74f8486ac89631690b))


### Feature


* feat: fix bugs with init and create, testing, partial implementation of status command ([`e069dbd`](https://github.com/groc-prog/pyneo4j-ogm/commit/e069dbdf80e3d3e0c1b460338b3b8d54311adde9))


* feat: add create command ([`8d509d4`](https://github.com/groc-prog/pyneo4j-ogm/commit/8d509d4e64ea505609de262519072d32e937679d))


* feat: add init command for initializing migrations ([`bd07e09`](https://github.com/groc-prog/pyneo4j-ogm/commit/bd07e09ea83acb9e716afe92764b724d50387f6b))


* feat: setup argparse with cli options ([`5294f92`](https://github.com/groc-prog/pyneo4j-ogm/commit/5294f9293fbed479955db8e466a21836dc01aa15))


* feat: basic migration dir structure ([`30c3c12`](https://github.com/groc-prog/pyneo4j-ogm/commit/30c3c126808990718ef6715fa0da77cd212d86a9))


### Fix


* fix: fix schema missing indexes/constraints if schemas reference each other ([`eb4d666`](https://github.com/groc-prog/pyneo4j-ogm/commit/eb4d666c94b326d81c9aa2d6c61fa6ee0bee5e08))


* fix: update CustomGenerateJsonSchema class to add index/constraint info ([`2a64464`](https://github.com/groc-prog/pyneo4j-ogm/commit/2a644646d765b3c0e1facb9798cba97c098fb371))


* fix: add missing index/constraint to model schema ([`01e2a9d`](https://github.com/groc-prog/pyneo4j-ogm/commit/01e2a9d8e0639f3e20cd3228685cd2b55684f1f2))


* fix: use enum values for string representation of RelationshipProperty ([`8889c62`](https://github.com/groc-prog/pyneo4j-ogm/commit/8889c62bd12df45bd306055b8c02d6c70554d03f))


* fix: fix relationship properties always being included in serialization in V1 ([`2ba47b9`](https://github.com/groc-prog/pyneo4j-ogm/commit/2ba47b9def3ecb10b3c4826c20783387f5e9800e))


* fix: only use CustomGenerateJsonSchema when IS_PYDANTIC_V2 is true, check exclude before adding id and element_id ([`3f621f6`](https://github.com/groc-prog/pyneo4j-ogm/commit/3f621f6e454bf044663c580a4d4544973e1c6b40))


* fix: implement custom GenerateJsonSchema class for v2 schema generation ([`fff7fea`](https://github.com/groc-prog/pyneo4j-ogm/commit/fff7fea558126f3722b66b5d510e4ea18f2ab940))


* fix: fix schema generation for pydantic v1 ([`13cbde8`](https://github.com/groc-prog/pyneo4j-ogm/commit/13cbde84b8b80c0803eecdd8aa7a9ecc4f2bdc25))


* fix: update schema generation ([`abe2035`](https://github.com/groc-prog/pyneo4j-ogm/commit/abe2035f7906cae3f4dda536bb3d3c5271a25f74))


* fix: fix issue where serialization would not work if nodes for relationship properties where fetched ([`4d0aa1e`](https://github.com/groc-prog/pyneo4j-ogm/commit/4d0aa1e27b0819cb194649dacb5ecdd8f23768c5))


### Refactor


* refactor: adjust exports from __init__.py ([`5026a93`](https://github.com/groc-prog/pyneo4j-ogm/commit/5026a93071d67c0101c638cf6f84ee31ae7ea213))


* refactor: implement model_serializer instead of overwriting methods ([`cfd8e0e`](https://github.com/groc-prog/pyneo4j-ogm/commit/cfd8e0e61b2c220e4adb20ae6616310555ccc440))


* refactor: adjust validation for custom pydantic types and dict/json conversion for pydantic v2 ([`5c4b61c`](https://github.com/groc-prog/pyneo4j-ogm/commit/5c4b61c6c9d8ead5b5fc58121b27e932c328d401))


* refactor: adjust validation for custom pydantic types and dict/json conversion ([`cfe9f03`](https://github.com/groc-prog/pyneo4j-ogm/commit/cfe9f03e714bd56c42bd65e2ebb6e814e926c7d3))


* refactor: remove arbitrary_types_allowed and add custom type for RelationshipProperty ([`0c59e73`](https://github.com/groc-prog/pyneo4j-ogm/commit/0c59e73c1103f9ead86dac42b3451c057c247bbb))



## What's Changed in v0.4.0 (2023-12-13)




### Documentation


* docs: update bookmark docs ([`38f1b13`](https://github.com/groc-prog/pyneo4j-ogm/commit/38f1b13052c0eea2a98cb0f18cde9203ece600db))


* docs: adjust index/constraint docs ([`5ebc419`](https://github.com/groc-prog/pyneo4j-ogm/commit/5ebc419fe54cdfff999880443e97fcd3a7f3c7c0))


* docs: update title ([`3054f2f`](https://github.com/groc-prog/pyneo4j-ogm/commit/3054f2f1a14551076e79cdf00db543c440fbbc35))


* docs: update docs for now serialization ([`7102cb8`](https://github.com/groc-prog/pyneo4j-ogm/commit/7102cb8ebb224897e298056fbd9e09921d24caab))


### Feature


* feat: add bookmark support for client and model methods ([`305bceb`](https://github.com/groc-prog/pyneo4j-ogm/commit/305bcebadf8c8aa77fb320d9059def3d785ae51e))


* feat(exceptions): remove ModelImportFailure exception ([`eec9eb4`](https://github.com/groc-prog/pyneo4j-ogm/commit/eec9eb4e6719369987235fb8b2330c7709e59247))


* feat(settings): remove exclude_from_export setting ([`5ef3cca`](https://github.com/groc-prog/pyneo4j-ogm/commit/5ef3ccaec1b1167765ae91bf33689bab01888c07))


* feat: exclude element_id and id before writing _db_properties ([`caf9763`](https://github.com/groc-prog/pyneo4j-ogm/commit/caf9763dd36a0293f4240189692202fb3b055e5e))


* feat(ModelBase): take exclude, include and by_alias arguments into account before adding element_id or id ([`b3fd01d`](https://github.com/groc-prog/pyneo4j-ogm/commit/b3fd01dbedb27e58150da32f3591f170697fd5ba))


* feat(ModelBase): include element_id and id fields in pydantics serialization methods ([`ea01cf5`](https://github.com/groc-prog/pyneo4j-ogm/commit/ea01cf560397160ab85490de635014eb8b90179f))


### Performance


* perf: optimize RelationshipProperty queries ([`f614ee4`](https://github.com/groc-prog/pyneo4j-ogm/commit/f614ee4d1bca33ad04f6c7c0673f0cc2affb8f0b))


* perf: optimize node and relationship queries ([`ecbb6e6`](https://github.com/groc-prog/pyneo4j-ogm/commit/ecbb6e60d5f4c200de18fe18dbb5f5c565e0c370))


### Refactor


* refactor: update logging ([`a8ef299`](https://github.com/groc-prog/pyneo4j-ogm/commit/a8ef299d82b1d35bc93f6dec86ccc8ae055c5b55))


* refactor(ModelBase): improve logging ([`e5711ee`](https://github.com/groc-prog/pyneo4j-ogm/commit/e5711ee369511f6865694a442d97372f80185593))


* refactor: remove unused IndexType enum ([`57afc4a`](https://github.com/groc-prog/pyneo4j-ogm/commit/57afc4adbcaf582324e8c043696eef870c4ae8af))


* refactor(Pyneo4jClient): split up index types into separate methods ([`1ec4d81`](https://github.com/groc-prog/pyneo4j-ogm/commit/1ec4d811731fa8f7d98d6aec748b292d69ac26d1))



## What's Changed in v0.3.0 (2023-11-30)




### Documentation


* docs: update supported pydantic versions in docs ([`5260cc5`](https://github.com/groc-prog/pyneo4j-ogm/commit/5260cc54443352461ddf532653bde5dcbc9edaab))


### Feature


* feat: update remaining codebase to pydantic v2, rename __settings__ to _settings ([`b4236a6`](https://github.com/groc-prog/pyneo4j-ogm/commit/b4236a6c6ab8fb85622261b5cdaf4bd2333dccdb))


* feat: update settings to pydantic v2 ([`a60ca78`](https://github.com/groc-prog/pyneo4j-ogm/commit/a60ca78c6cbcd0298eab13867aa7cebbe218638d))


* feat: update validators to pydantic v2 ([`08a3641`](https://github.com/groc-prog/pyneo4j-ogm/commit/08a36410cf9f577a1368fc6cc97f2737ab664ca5))


* feat: add pydantic utils for backwards compatibility ([`9a85d4a`](https://github.com/groc-prog/pyneo4j-ogm/commit/9a85d4a8ffef74ce7be28606ddc1dd719622186e))


### Fix


* fix(WithOptions): fix typing issue ([`8228964`](https://github.com/groc-prog/pyneo4j-ogm/commit/8228964d82f39733d356b4175b52890d866f45c2))


* fix(RelationshipModel): use _deflate() instead of model_dump ([`1198602`](https://github.com/groc-prog/pyneo4j-ogm/commit/1198602e6119df225607d28a1cdcecdb013e6767))


* fix(NodeModel): implement dirty??? hack for pydantic fields not getting initialized separately anymore, use _deflate instead of model_dump ([`ed106ba`](https://github.com/groc-prog/pyneo4j-ogm/commit/ed106ba020110e4b0f0edeefba40572aae0800ef))


* fix(WithOptions): fix breaking changes in v2 ([`3484ed6`](https://github.com/groc-prog/pyneo4j-ogm/commit/3484ed6af294ebc558e000f909ca21976dffb9dc))


* fix(validators): fix breaking change in validator return value ([`857dd93`](https://github.com/groc-prog/pyneo4j-ogm/commit/857dd937eeab909f7c0305fe9da788c4e34e2433))


* fix(NodeModel): register relationship properties correctly with pydantic v2 ([`68f415f`](https://github.com/groc-prog/pyneo4j-ogm/commit/68f415f9ca21d096f41ba5a35364011c53318e0a))


* fix(ModelBase): fix root validator ([`33f43bd`](https://github.com/groc-prog/pyneo4j-ogm/commit/33f43bd36b83586f9b6c68073f4d13289a67598a))


* fix: fix pydantic utils typings ([`65feb25`](https://github.com/groc-prog/pyneo4j-ogm/commit/65feb2501eab6c79e3b440d397cca66c87e0e66a))


### Performance


* perf(NodeModel): stop looping over model if auto-fetch models have been found ([`efee0fc`](https://github.com/groc-prog/pyneo4j-ogm/commit/efee0fcf837a50afe44f93af48ddb39edfea0434))


### Refactor


* refactor(RelationshipProperty): use parse_model() instead of model.validate() ([`1a27569`](https://github.com/groc-prog/pyneo4j-ogm/commit/1a275696bb413b0c0c911ee62424728342a8642d))



## What's Changed in v0.2.0 (2023-11-29)




### Documentation


* docs: update features ([`e3bc559`](https://github.com/groc-prog/pyneo4j-ogm/commit/e3bc559e17a7f0d172d66559e0fc9d6cc5e36ecb))


* docs: update code comments ([`a94b3fe`](https://github.com/groc-prog/pyneo4j-ogm/commit/a94b3fe2be8166d671f1ebbbdf52855910b16c02))


* docs: add special projection values to docs ([`896f3fa`](https://github.com/groc-prog/pyneo4j-ogm/commit/896f3fab81fc577c8d588cad6781a9dcb341454a))


* docs: update docs to recent changes ([`68d821e`](https://github.com/groc-prog/pyneo4j-ogm/commit/68d821e093ce3e8704710224159d74ac34a2c9ac))


* docs: update docstrings ([`326f4cd`](https://github.com/groc-prog/pyneo4j-ogm/commit/326f4cd08890c95c110d0002f0d10a76f4679db7))


* docs: update docstrings for ModelBase, Pyneo4jClient and NodeModel classes ([`dc3ca1f`](https://github.com/groc-prog/pyneo4j-ogm/commit/dc3ca1f19e8dfa1a1bcb31a534b4bbaefd2ef742))


* docs: adjust docstrings ([`a44f95f`](https://github.com/groc-prog/pyneo4j-ogm/commit/a44f95f1dece837f60a3e1db7baf692e2c68caa9))


* docs: Update todos ([`37be36e`](https://github.com/groc-prog/pyneo4j-ogm/commit/37be36e3cff46ae2a77c826cfdd800e6c2dcfd77))


* docs: add env variable for disabling logger to module docstring ([`a79c7ee`](https://github.com/groc-prog/pyneo4j-ogm/commit/a79c7ee5bbce97789517f24387afaad8db83c7f1))


### Feature


* feat: add type for projections ([`8f8af8a`](https://github.com/groc-prog/pyneo4j-ogm/commit/8f8af8a129b6fe762970ddf865dd42c9cde0e805))


* feat: add option to raise exception if find_one, update_one, delete_one or disconnect methods do not find any matches ([`c6a2901`](https://github.com/groc-prog/pyneo4j-ogm/commit/c6a29016bb4918697e819c841cbf929ef8551442))


* feat(RelationshipProperty): the `replace()` method now moves all relationships between current and old node to new node ([`0e37bf3`](https://github.com/groc-prog/pyneo4j-ogm/commit/0e37bf34e86ba6c004dc77226521d3e687d9cfb5))


* feat: handle sync and async hooks differently, relationships method now supports filters, projections and options ([`27901e4`](https://github.com/groc-prog/pyneo4j-ogm/commit/27901e4ec5a10e1e7933d5ec83a6109a6a4e4ff5))


* feat(NodeModel): exclude relationship properties from modified_properties, auto-fetch now raises an exception if a relationship or node model which is auto fetched is not registered ([`873e7ac`](https://github.com/groc-prog/pyneo4j-ogm/commit/873e7acfc59454a50eb0e5bce30a875c54114d7e))


* feat(RelationshipProperty): relationship() has been renamed to relationships(), now returns a list of relationships instead of a single relationship or None ([`8bf70a7`](https://github.com/groc-prog/pyneo4j-ogm/commit/8bf70a70344a2f53820007a5c1ccd57c7410493b))


* feat(MultiHopFilter): support $direction filter for path ([`d740679`](https://github.com/groc-prog/pyneo4j-ogm/commit/d740679c07a3bb4088f55a94f76e4f5796e34606))


* feat(Pyneo4jClient): Rename Neo4jClient to Pyneo4jClient ([`cf71356`](https://github.com/groc-prog/pyneo4j-ogm/commit/cf71356e62fc7391c770665b10c09651503b9c3e))


### Fix


* fix: find_many queries now return correct results if options and projections are used together ([`63730fb`](https://github.com/groc-prog/pyneo4j-ogm/commit/63730fbf174d8d36bb2ee90a100469911876e051))


* fix: parse query result to model if raw result, prevent usage of lists with non primitive values ([`f600700`](https://github.com/groc-prog/pyneo4j-ogm/commit/f600700218544d871bc820de4d4d3b3ac035376e))


* fix(validators): change QueryDataTypes to Any to prevent pydantic from changing data type when validating filters ([`d195648`](https://github.com/groc-prog/pyneo4j-ogm/commit/d195648cc005bd0c9b676583189fc6080728148f))


* fix: st _id field in relationship when inflating ([`79dc118`](https://github.com/groc-prog/pyneo4j-ogm/commit/79dc118942a00f3822ca6fab57f0fe7264e37748))


* fix(NodeModel): raise UnregisteredModel exception if target model for find_connected_nodes has not been registered ([`ae92801`](https://github.com/groc-prog/pyneo4j-ogm/commit/ae928013a62acbe1c03bb5c7a8fdb61a84ad489f))


* fix(projections, auto-fetch): fix non-distinct values being returned when using projections, fix missing auto-fetched nodes when multiple returned models were connected to the same auto-fetched node ([`7170623`](https://github.com/groc-prog/pyneo4j-ogm/commit/717062376615788c078dbc416db8af8f0e7b4dd4))


* fix(typings): add typing-extensions as dependency, adjust types so required keys are actually required ([`c65f236`](https://github.com/groc-prog/pyneo4j-ogm/commit/c65f236316b8e4b0c2211efabfdddf1fcf9485fd))


* fix(validators): add default values and adjust types for QueryOptionModel validator ([`a83f7e7`](https://github.com/groc-prog/pyneo4j-ogm/commit/a83f7e79c59973373889d5d33f16fb764f9329d5))


* fix: Remove unused if statement in __eq__ method, raise ModelImportFailure exc if id is missing in dict ([`435c971`](https://github.com/groc-prog/pyneo4j-ogm/commit/435c971342fd0c64c0ff4e48ce5443265c480ea6))


* fix: fix typings for RelationshipFilters and RelationshipPropertyFilters ([`24458bd`](https://github.com/groc-prog/pyneo4j-ogm/commit/24458bd62f0d8778ec5fa9c7bdef0c5617eecf9b))


### Refactor


* refactor(RelationshipProperty): use Optional instead of Union with None ([`2d381b9`](https://github.com/groc-prog/pyneo4j-ogm/commit/2d381b9e475bd9fbfa9c5725fd8d2abb0749a73d))


* refactor(RelationshipProperty): pass source node to relationship-property hooks instead of self ([`539f6f9`](https://github.com/groc-prog/pyneo4j-ogm/commit/539f6f99ca9636a6cd5d0a176fddce6dc467c9e0))


* refactor: rename NoResultsFound to UnexpectedEmptyResult ([`593ac58`](https://github.com/groc-prog/pyneo4j-ogm/commit/593ac587106d7a1d250bd4ad6fe624185f896d7b))


* refactor: use LiteralString from typing_extensions package to stay compatible with python &lt; 3.11 ([`05c344d`](https://github.com/groc-prog/pyneo4j-ogm/commit/05c344dd1d9e7afdb12d15dd28d11d3d0bc01494))


* refactor(RelationshipProperty): add some checks for empty queries adn ensure_alive method, refactor find_connected_nodes method ([`2a848fc`](https://github.com/groc-prog/pyneo4j-ogm/commit/2a848fc7fefd926b1600766c7df84209244a6eb9))


* refactor(NodeModel): split class name into substrings when falling back to auto labels ([`3992266`](https://github.com/groc-prog/pyneo4j-ogm/commit/3992266e185ac2be4d9f5b63106bbd10c96323ff))


* refactor(ModelBase): Change modified_properties from list to set ([`597100f`](https://github.com/groc-prog/pyneo4j-ogm/commit/597100ff3d6e367d76c6be287bb261d364172ea2))


* refactor(property_options): remove unused magic method ([`75981f3`](https://github.com/groc-prog/pyneo4j-ogm/commit/75981f33e9949cb7c21f85cdc74cebf84420d496))


* refactor: change relationship variable from build param to function param ([`6d331b7`](https://github.com/groc-prog/pyneo4j-ogm/commit/6d331b7fb8a4f4b8af1feb8a33b88ac20295e42d))



## What's Changed in v0.1.0 (2023-11-06)




### Documentation


* docs: Update todos and future features ([`96f350b`](https://github.com/groc-prog/pyneo4j-ogm/commit/96f350bc27c85d4005e58f9a7a1b450af88be4be))


* docs: Documentation for remaining methods/functionality ([`31dca97`](https://github.com/groc-prog/pyneo4j-ogm/commit/31dca971a21425f978f2028bd72453b676fa0645))


* docs(RelationshipProperty): Add docs for RelationshipProperty class ([`df0153f`](https://github.com/groc-prog/pyneo4j-ogm/commit/df0153fc3ced13950e0da2559a3224c02afb68f3))


* docs: Fix wrong method name in example ([`6ceffe8`](https://github.com/groc-prog/pyneo4j-ogm/commit/6ceffe82e1776b601cdb1bfef6aa63abea7e89c2))


* docs: Add remaining model methods ([`324a549`](https://github.com/groc-prog/pyneo4j-ogm/commit/324a549031053b219d6f5b6f76d5cb8629820ea6))


* docs: Update todos ([`bc09628`](https://github.com/groc-prog/pyneo4j-ogm/commit/bc0962881a228c43ccca956b0a5a06b55a1b91a7))


* docs: Add todos ([`35aa56a`](https://github.com/groc-prog/pyneo4j-ogm/commit/35aa56a85313961e09c90dec56dde387fe872a74))


* docs: Add docs for more model methods ([`4d853f5`](https://github.com/groc-prog/pyneo4j-ogm/commit/4d853f5152c998d2f6db303b4f03855cea7a9797))


* docs: Add further todos ([`5a4fde0`](https://github.com/groc-prog/pyneo4j-ogm/commit/5a4fde06c31d914799fd61d70f03262a64adcec3))


* docs: Fix typos ([`0d19b64`](https://github.com/groc-prog/pyneo4j-ogm/commit/0d19b64a94aee5896ad10e0b9664a540f45f856e))


* docs: Add documentation for find_one and find_many methods ([`57c5b58`](https://github.com/groc-prog/pyneo4j-ogm/commit/57c5b58270336910d3e2cb7f94fc55305dc0fbe1))


* docs: Update projection docs for node and relationship models ([`5a753bb`](https://github.com/groc-prog/pyneo4j-ogm/commit/5a753bbbb11eaaec879fc3e1474d280cc6fc4b3c))


* docs: Update docs to include new features, rewrite some outdated info ([`d45c7da`](https://github.com/groc-prog/pyneo4j-ogm/commit/d45c7da54e427d32a943afc051cd460d5020215a))


* docs: Add todo&#39;s ([`d2dd477`](https://github.com/groc-prog/pyneo4j-ogm/commit/d2dd477b8aaeb5559a986101856817c01d26ffcb))


* docs: Update todos ([`0f88c64`](https://github.com/groc-prog/pyneo4j-ogm/commit/0f88c64dd321b0ba61381b879344731c3500bae9))


* docs: Update TODO&#39;s ([`2bff72a`](https://github.com/groc-prog/pyneo4j-ogm/commit/2bff72a33875b952787cf7414f770769de087515))


* docs: Finished first draft ([`b0647d9`](https://github.com/groc-prog/pyneo4j-ogm/commit/b0647d9e7ea22b80070a7772c72b7b58e34fe0c1))


* docs: Add some missing docs ([`b1eba4a`](https://github.com/groc-prog/pyneo4j-ogm/commit/b1eba4a48aed0a94a831a3a85c21304238461a57))


* docs: Add todo&#39;s and feature for future updates ([`ef42457`](https://github.com/groc-prog/pyneo4j-ogm/commit/ef424573f6e194d2d5dfaaef1fa7e4cf6e864220))


* docs: Remove repeated client connecting from code snippets ([`cf1cd75`](https://github.com/groc-prog/pyneo4j-ogm/commit/cf1cd75d57996da101a5a6d7e5cdac36f4469acf))


* docs: Update docs ([`bc6cb96`](https://github.com/groc-prog/pyneo4j-ogm/commit/bc6cb9603d4a7a1ca4493433d45f5980ca0b9861))


* docs: Remove todos ([`a50fc07`](https://github.com/groc-prog/pyneo4j-ogm/commit/a50fc07afa3b9662176ccc8b68de36f37a16a2fe))


* docs: Add todos ([`d9dae1f`](https://github.com/groc-prog/pyneo4j-ogm/commit/d9dae1fc26541ec849265050547d4734fefbbcaa))


* docs: Worki n progress ([`4ea0df5`](https://github.com/groc-prog/pyneo4j-ogm/commit/4ea0df5d4c342c90cc55a6d9956fe7d4802c3984))


* docs: Basic outline for docs content ([`e9c35ad`](https://github.com/groc-prog/pyneo4j-ogm/commit/e9c35ad07c6fd1e69cfcd32c97fbfd3306d2cc13))


* docs: Update README.md ([`4360f23`](https://github.com/groc-prog/pyneo4j-ogm/commit/4360f2397ba563932ea8e0b702569350a184a0a4))


* docs: Filters and query options ([`e2972f2`](https://github.com/groc-prog/pyneo4j-ogm/commit/e2972f23748a88dd265c3034ad68a2c888687491))


* docs: Pattern filters ([`8eeda0b`](https://github.com/groc-prog/pyneo4j-ogm/commit/8eeda0b783966a669f9ba7806bf8052a90085be7))


* docs: Basic filter operators ([`c1977f5`](https://github.com/groc-prog/pyneo4j-ogm/commit/c1977f5d9c64cc94232414e2537b03bdc2e7e3b9))


* docs: Docs for relationship properties ([`2052727`](https://github.com/groc-prog/pyneo4j-ogm/commit/20527279e579df1953de7db685086f60c5cbe0ce))


* docs: Docs for relationship models and properties ([`85edca1`](https://github.com/groc-prog/pyneo4j-ogm/commit/85edca1edfa17aada78210a415408b3bc7f444ae))


* docs: PLEASE MAKE IT STOP ([`dc78b8f`](https://github.com/groc-prog/pyneo4j-ogm/commit/dc78b8f4832ce331e118dd74cf10751bbaaaa2af))


* docs: Node model docs ([`5315285`](https://github.com/groc-prog/pyneo4j-ogm/commit/53152852c127b9cec4aa4ae3b4b10ada7d42a6cb))


* docs: Documentation for getting started and node properties/settings ([`65011c9`](https://github.com/groc-prog/pyneo4j-ogm/commit/65011c9e3084133cc76ff375aa56e443f840f642))


* docs: README content outlining ([`31d3103`](https://github.com/groc-prog/pyneo4j-ogm/commit/31d3103a05129fa1265800526fba3df3b559fca8))


* docs: Test formatting ([`de7e38a`](https://github.com/groc-prog/pyneo4j-ogm/commit/de7e38a0291cce5434e4da04ee6c3b0f5ac7ec84))


* docs: Add missing raises ([`2511185`](https://github.com/groc-prog/pyneo4j-ogm/commit/2511185933cabedbf83314024d804a194bee28af))


* docs: Property getter docstring ([`f045539`](https://github.com/groc-prog/pyneo4j-ogm/commit/f045539666aad0d51b43026f900be9d49a1ab38e))


* docs(filters): Docs for QueryBuilder class ([`962cb62`](https://github.com/groc-prog/pyneo4j-ogm/commit/962cb6212dcdf03e920367933ac5ba1779c13478))


* docs: Fixed typos ([`2e82e1e`](https://github.com/groc-prog/pyneo4j-ogm/commit/2e82e1e389483f04ff7a577cdaec6bc40e8c8626))


### Feature


* feat(client): Enforce Neo4j version 5+ when connecting ([`14a022b`](https://github.com/groc-prog/pyneo4j-ogm/commit/14a022b3d353a080aa08657a129fdcd415a64088))


* feat(find_one, find_many, find_connected_nodes): Allow for partial auto-fetch for defined models ([`242c90e`](https://github.com/groc-prog/pyneo4j-ogm/commit/242c90e3f598a1a9418a9292d856d7da8f694502))


* feat: Rename node_projection to build_projections and add projections to RelationshipModel, remove unnecessary DISTINCT keywords ([`26b5007`](https://github.com/groc-prog/pyneo4j-ogm/commit/26b500750a94a72b70d9b5bfa633bdb7dd48c148))


* feat: Projections and auto_fetch_nodes for find_connected_nodes method on relationship properties ([`3ad9ed8`](https://github.com/groc-prog/pyneo4j-ogm/commit/3ad9ed84da663402e412c1f66b60507c9f39d91b))


* feat: Add hooks for relationship property methods ([`0ac0fdb`](https://github.com/groc-prog/pyneo4j-ogm/commit/0ac0fdb48fc2eb0e4659c60aaec57b007078a776))


* feat: Rename pattern $not operator to $exists ([`5081eee`](https://github.com/groc-prog/pyneo4j-ogm/commit/5081eeeae507e29b883e3c3d17912249945d8730))


* feat: Projections and auto-fetch for find_connected_nodes method ([`9033afb`](https://github.com/groc-prog/pyneo4j-ogm/commit/9033afb20e793ef678aa34c81f4a05b64d8ba62d))


* feat: Separated node projections from query filters ([`581978b`](https://github.com/groc-prog/pyneo4j-ogm/commit/581978b6f135072a44cafc0195eb35f0ff9527c0))


* feat: Extended query builder for node projections ([`c3ec579`](https://github.com/groc-prog/pyneo4j-ogm/commit/c3ec579f9eb42a4b36c2ec84a6310ce4cd26a939))


* feat: Resolve queries using COLLECT ([`d69616a`](https://github.com/groc-prog/pyneo4j-ogm/commit/d69616a92635bf52cf4cb3748ce114165db555df))


* feat: Cardinality for relationships ([`2398796`](https://github.com/groc-prog/pyneo4j-ogm/commit/23987967921649a6acd75e4f1ef05ab07acd30cc))


* feat: Client method for registering cardinality for relationship ([`787692a`](https://github.com/groc-prog/pyneo4j-ogm/commit/787692aebedb03f14999d91293a879a4ac90eba4))


* feat: Option to skip index and constraint creation on model registering ([`0d62f76`](https://github.com/groc-prog/pyneo4j-ogm/commit/0d62f76400b14f57cacb33113ea5462652db06b3))


* feat: Change logging to lib logger ([`f907d28`](https://github.com/groc-prog/pyneo4j-ogm/commit/f907d28590d210d3e4dcc59252e5839e359ff5b7))


* feat: Add custom logger ([`75464d4`](https://github.com/groc-prog/pyneo4j-ogm/commit/75464d4c9d5ece962435cccbb05802aef7c12fdc))


* feat: Auto fetching nodes possible for find_one and find_many methods on NodeModel classes ([`3f87cd4`](https://github.com/groc-prog/pyneo4j-ogm/commit/3f87cd4bbdc68d4f261b9c5e9ea364b72af2c3cf))


* feat: Add nodes property to RelationshipProperty which will hold auto-fetched nodes ([`5b77bd5`](https://github.com/groc-prog/pyneo4j-ogm/commit/5b77bd5410c7e2b5e000a307ad557f5d78ddb32e))


* feat: Add auto-fetch setting and todo&#39;s in README.md ([`9f27538`](https://github.com/groc-prog/pyneo4j-ogm/commit/9f27538995cc4e10052076f3716e8942d025fd4a))


* feat: Convert fallback label to PascalCase before saving ([`eded4cb`](https://github.com/groc-prog/pyneo4j-ogm/commit/eded4cb866d75be1e4def2528a8f1d69411435ba))


* feat: Add query options to find_connected_nodes method for nodemodel ([`00e3561`](https://github.com/groc-prog/pyneo4j-ogm/commit/00e35619d9931acd381e82bb77e6f5d003c29043))


* feat: Add relationship filters to relationship property find_connected_nodes method ([`e8e8e4f`](https://github.com/groc-prog/pyneo4j-ogm/commit/e8e8e4f8726876b76a1fd9ad545ed306ce7b036d))


* feat: find_connected_nodes method for NodeModel instance with relationship filters ([`6a87fe6`](https://github.com/groc-prog/pyneo4j-ogm/commit/6a87fe6876fb1ba6c3df762775d758d33c7ce6d1))


* feat: Query builder method for getting nodes with multiple hops ([`8460632`](https://github.com/groc-prog/pyneo4j-ogm/commit/8460632e78e695b48a7dfd62f5c8b5dbd93c739d))


* feat: Validator and type hints for multi hop filters ([`5243658`](https://github.com/groc-prog/pyneo4j-ogm/commit/52436582108f39675cf2ae68095d321e281b1754))


* feat: Pattern filters ([`b546bf5`](https://github.com/groc-prog/pyneo4j-ogm/commit/b546bf5e8c0f2770756d05fe4069827b536a9b04))


* feat: Resolve Path classes returned from query to db models ([`8571d08`](https://github.com/groc-prog/pyneo4j-ogm/commit/8571d08d4cd87b337d035bb691d6aafb9e5d5c80))


* feat: Hooks WIP, typings are lost when setting hooks decorator ([`0b320ae`](https://github.com/groc-prog/pyneo4j-ogm/commit/0b320ae5b82884eeb0c3ef1bea68da1ffe15ad43))


* feat: Import/export model from/to dict ([`5737490`](https://github.com/groc-prog/pyneo4j-ogm/commit/5737490b9d7dfdd77b6b3bffb63d7a4ab35950d9))


* feat: Export model to dict method, moved shared logic to ModelBase class ([`95a6606`](https://github.com/groc-prog/pyneo4j-ogm/commit/95a66066212049f68d5313416d81b5b97fbe21a0))


* feat: Relationship and node match builder ([`2bb0b2d`](https://github.com/groc-prog/pyneo4j-ogm/commit/2bb0b2defbf172a6dcc0a6f3209260f3964f1003))


* feat: Method for building query options ([`9dd7564`](https://github.com/groc-prog/pyneo4j-ogm/commit/9dd7564ebfced475ba82955e55acf2998ab6e522))


* feat: WIP normalizing query filters ([`864c82c`](https://github.com/groc-prog/pyneo4j-ogm/commit/864c82cc0c965dbccb46ed0b25fd41cd903a8b26))


* feat: Remove find_connected_nodes from NodeModel ([`ade25c1`](https://github.com/groc-prog/pyneo4j-ogm/commit/ade25c1cb0f0a6cc70511cb15c807bfe9aabc406))


* feat: Added register models by dir name, but somehow it does not work when calling register_models first?????????? ([`8200546`](https://github.com/groc-prog/pyneo4j-ogm/commit/820054616fa89d73aa0d868bc7f44b7d9732cef5))


* feat: Load models from directory path ([`93173b1`](https://github.com/groc-prog/pyneo4j-ogm/commit/93173b137878bd0112c49a7c95a72526a83cfa23))


* feat: find_connected_node method for NodeModel ([`93a93e1`](https://github.com/groc-prog/pyneo4j-ogm/commit/93a93e14909a936f0a3978b3aa8de3ba67124221))


* feat: Refresh method for relationship, fixed logging for node refresh method ([`58aedd4`](https://github.com/groc-prog/pyneo4j-ogm/commit/58aedd48be1628094086e3c51d25474b88c27a33))


* feat: Refresh method for node model ([`b424a8f`](https://github.com/groc-prog/pyneo4j-ogm/commit/b424a8fc8352b2b15c2b1b7c8e86758af66a0741))


* feat: find_connected_nodes method for properties, add new items to task list ([`816b642`](https://github.com/groc-prog/pyneo4j-ogm/commit/816b642e68eb43feceba9d646336837701c79975))


* feat: replace method for relationship property ([`e555888`](https://github.com/groc-prog/pyneo4j-ogm/commit/e555888310bb823d55810d1cf1479835cfb1f597))


* feat: Remove upsert in favour of creating new instances since validation would prevent upsert if required properties were not preset ([`a57bbe7`](https://github.com/groc-prog/pyneo4j-ogm/commit/a57bbe70f185ee296d9615fff8fa2dd3d2f70c9c))


* feat: Method for deleting all connected nodes ([`bb2b643`](https://github.com/groc-prog/pyneo4j-ogm/commit/bb2b643063404db93c5d984bcb200546c643a954))


* feat: Method for deleting all relationships between source and target node ([`4745f44`](https://github.com/groc-prog/pyneo4j-ogm/commit/4745f4426392f6578c03c81097cf4ca6dfbaf9f0))


* feat: Method for connecting node to relationship ([`eacc346`](https://github.com/groc-prog/pyneo4j-ogm/commit/eacc346b58d3e1642853ac6bf8d4411ee57bae61))


* feat: Relationship property for defining relationships on NodeModel classes ([`cf23ba5`](https://github.com/groc-prog/pyneo4j-ogm/commit/cf23ba5efb810fccae32c4fc9b0ab74286a3ac74))


* feat: Make register_models accept both node and relationship models ([`81f841e`](https://github.com/groc-prog/pyneo4j-ogm/commit/81f841eecfcc3dc3bdc5cfde9b10caa467e3093e))


* feat: Remove ref from WithOptions function ([`bd30166`](https://github.com/groc-prog/pyneo4j-ogm/commit/bd30166b3fe481c55b9aac4e6a8f2eeffb57d7b3))


* feat: Add pattern filter expressions for nodes, still needs to be tested for relationships ([`6d0e746`](https://github.com/groc-prog/pyneo4j-ogm/commit/6d0e7466f7e1ef1c18d1353ada4f3171c35036e9))


* feat: Add backticks to relationship and node type/labels to prevent breaking when non-alphabetic or labels/type with spaces is passet ([`723b20d`](https://github.com/groc-prog/pyneo4j-ogm/commit/723b20df79d36afe11ec778fa7ed2f1297e549d6))


* feat: Validator and type hints for pattern operator ([`425c54f`](https://github.com/groc-prog/pyneo4j-ogm/commit/425c54fd94406892e5e7ceba5a6c7655a0f2a30a))


* feat: Methods for getting start and end node for a relationship ([`4c02fa2`](https://github.com/groc-prog/pyneo4j-ogm/commit/4c02fa27843321fa8aa8307aa896852ad4cfe61c))


* feat: Basic relationship query methods ([`6b377b3`](https://github.com/groc-prog/pyneo4j-ogm/commit/6b377b313cd303d0855b35dd47144f4cb9e676a4))


* feat: Relationship class ([`f9e0fa2`](https://github.com/groc-prog/pyneo4j-ogm/commit/f9e0fa2a744184020bd9e8a6cadfbc97ebc1228a))


* feat: Added type hints to expressions, fixed wrong expression validator for $size operator ([`a615d72`](https://github.com/groc-prog/pyneo4j-ogm/commit/a615d7211737d696054fda7fc502f5af4967a3ec))


* feat: Add number of deleted nodes to delete_one and delete_many as return value ([`a8fb1c1`](https://github.com/groc-prog/pyneo4j-ogm/commit/a8fb1c132f8574ef45e80292f4d7ce77785a38ec))


* feat: Implement batch query context manager ([`96f6371`](https://github.com/groc-prog/pyneo4j-ogm/commit/96f63718b0cb29a92ea9a82b8566d9482855688f))


* feat: Update and delete methods, to be tested ([`88563e0`](https://github.com/groc-prog/pyneo4j-ogm/commit/88563e0b4dd41d75218595b3fa5ff6ed2d2583f1))


* feat: update_one method for updating the first encountered node ([`bb601c2`](https://github.com/groc-prog/pyneo4j-ogm/commit/bb601c2dc94a1426c9e56c62259dbb84ac1b1a82))


* feat: Register defined options for a property when registering model with client ([`6535505`](https://github.com/groc-prog/pyneo4j-ogm/commit/6535505d3746749aa6644e98dbfd75178a39aeb5))


* feat: Update to different index types ([`1fc776a`](https://github.com/groc-prog/pyneo4j-ogm/commit/1fc776a2da9f442d0c2d620d8820f79ea81cff21))


* feat: Createing constraints and indexes ([`0dcb321`](https://github.com/groc-prog/pyneo4j-ogm/commit/0dcb3211d8f1c14ac47a3581d11289c145a99fb8))


* feat: Add ref property to class returned by WithOptions ([`fbec028`](https://github.com/groc-prog/pyneo4j-ogm/commit/fbec028183e150410d5ae0f4ce57a23a36f0e8fb))


* feat: Method for building query options ([`679e64b`](https://github.com/groc-prog/pyneo4j-ogm/commit/679e64b20bb1c8afa84c33eff2735f5e13c86a53))


* feat: Query expression validator ([`3e0a132`](https://github.com/groc-prog/pyneo4j-ogm/commit/3e0a1322bcc516f26ae25a775736078255a85cfb))


* feat: find_many method for node, downgrade to python 3.10 ([`87ae35d`](https://github.com/groc-prog/pyneo4j-ogm/commit/87ae35dc53aaabad2ab4777a453ebcd41a11f97d))


* feat: Resolve database models if registered on client ([`58a0fe5`](https://github.com/groc-prog/pyneo4j-ogm/commit/58a0fe5c2d58801b5e190d6ca33ccc481c85eb72))


* feat: Resolving database model ([`37da856`](https://github.com/groc-prog/pyneo4j-ogm/commit/37da856ac4ed569d6bdd5b19cadec80531d5f749))


* feat: Node find_many method ([`a2a00cb`](https://github.com/groc-prog/pyneo4j-ogm/commit/a2a00cb6276b2cdc334d6804afb188fa1e4e9de6))


* feat: find_one method for returning first node match ([`2b89e62`](https://github.com/groc-prog/pyneo4j-ogm/commit/2b89e62ed3e41d9ac1d1f72132c40f0bfbacc0dc))


* feat: Basic operants for filtering properties ([`548ae9a`](https://github.com/groc-prog/pyneo4j-ogm/commit/548ae9a9151fd465c4774df1b601997acb860374))


* feat: BAsic operants working ([`46aa8a4`](https://github.com/groc-prog/pyneo4j-ogm/commit/46aa8a4b58b4a8aceceb7905e0f095f361763d10))


* feat: Builder for comparison operators ([`7aa08d2`](https://github.com/groc-prog/pyneo4j-ogm/commit/7aa08d25671392de8cce8545ed1207cfa7a8feb4))


* feat(OperantQueryBuilder): New concept, work in progress ([`b180d42`](https://github.com/groc-prog/pyneo4j-ogm/commit/b180d42edf8bcb9fbefe7dd51067007226840082))


* feat(QueryBuilder): Add $element_id operant ([`8f3c415`](https://github.com/groc-prog/pyneo4j-ogm/commit/8f3c415fb21e9f54bb68fb759a986cab594f3aac))


* feat(filters): Combined filter options $and, $or, $xor ([`e87e224`](https://github.com/groc-prog/pyneo4j-ogm/commit/e87e224ddd0699f7fa37cc988b7b1d648bbc09bc))


* feat(filters): Filters for $exists, $not and all other basic filters ([`3a6174f`](https://github.com/groc-prog/pyneo4j-ogm/commit/3a6174f38b9648340b1a80e55d5d22209105a97b))


* feat: Build relationship property on model init ([`59d0a96`](https://github.com/groc-prog/pyneo4j-ogm/commit/59d0a962347d605695a70f7d3eeaef7fb6810b06))


* feat(RelationshipProperty): WIP ([`b391ea0`](https://github.com/groc-prog/pyneo4j-ogm/commit/b391ea0f4c116eb2d73f6f5f5f238b89aa7a4b36))


* feat(Neo4jRelationship): Update/Delete methods ([`1e3fee2`](https://github.com/groc-prog/pyneo4j-ogm/commit/1e3fee25d77a9fd023235380578c6130a09ab8f2))


* feat(Neo4jNode): Delete node ([`9bd26bc`](https://github.com/groc-prog/pyneo4j-ogm/commit/9bd26bc3c2bed34a24f72ad77528846651f8a8b0))


* feat(Neo4jNode): Update method with modified fields ([`e58c8d6`](https://github.com/groc-prog/pyneo4j-ogm/commit/e58c8d62f4a8c40104ddb2ba247544351edac8b0))


* feat(utils): Merge ensure_alive and ensure_hydrated decorators to one ([`3d5d526`](https://github.com/groc-prog/pyneo4j-ogm/commit/3d5d526e1e17cca6d971673a7a7daba0a27cb8c2))


* feat(core): Logging, switches to privateattrs, create node instance method ([`27e986c`](https://github.com/groc-prog/pyneo4j-ogm/commit/27e986c84ac1a81fe3a745006d5c205442674bd9))


* feat(utils): Decorators for checking if a instance is hydrated/destroyed and validating model before writing to db ([`647671b`](https://github.com/groc-prog/pyneo4j-ogm/commit/647671bde13015218c405c19d359a61b48faab65))


* feat(typings): Added  better typings support ([`e7aab10`](https://github.com/groc-prog/pyneo4j-ogm/commit/e7aab1025fc26cd1421c8008666e9ba29a38298b))


* feat: Add core to exports ([`efa4d5b`](https://github.com/groc-prog/pyneo4j-ogm/commit/efa4d5ba1d66dc7949b9b5ca56a58590e08ea60a))


* feat(Neo4jRelationship, Neo4jNode): Define type/labels in model ([`303fb58`](https://github.com/groc-prog/pyneo4j-ogm/commit/303fb58ad05311c317db60f485ea54ace63a3bf5))


* feat(Neo4jNode): Inflate/deflate logic for nodes ([`a260a2d`](https://github.com/groc-prog/pyneo4j-ogm/commit/a260a2dc80fe5040f03ef681785762c9b8b67902))


* feat(Neo4jClient): Auth can now be provided with NEO4J_AUTH env var ([`ec77353`](https://github.com/groc-prog/pyneo4j-ogm/commit/ec773535dc407848f2fd1ca529421af70c17b2b4))


* feat(Neo4jRelationship): Inflate relationship instance to model instance ([`0a79b21`](https://github.com/groc-prog/pyneo4j-ogm/commit/0a79b21e06a0f029dfc57add97cce5422e289f7d))


* feat(Neo4jRelationship): Logic for deflating model to neo4j dict ([`44c7991`](https://github.com/groc-prog/pyneo4j-ogm/commit/44c7991f5de9eb109d27464e66d521e70879f0df))


* feat(WithOptions): Custom field for defining indexes and uniqueness constraint for property ([`7cfb420`](https://github.com/groc-prog/pyneo4j-ogm/commit/7cfb42003fadfa3b31d33a7cc520cccae5946692))


* feat(Neo4jClient): Methods for deleting all nodes/constraints and setting new constraints ([`e5a3844`](https://github.com/groc-prog/pyneo4j-ogm/commit/e5a3844b491e29b5f8fec8e925933ad2b3178040))


* feat(Neo4jClient): Client class for running queries against database ([`a181ffa`](https://github.com/groc-prog/pyneo4j-ogm/commit/a181ffaee9adfb37ddea1b63a1d14897e6443bfd))


* feat(docker): Docker compose file for testing ([`4034f36`](https://github.com/groc-prog/pyneo4j-ogm/commit/4034f36a098146758786c9464d6c5bd978bb836b))


* feat(gitignore): Add gitignore ([`73628bc`](https://github.com/groc-prog/pyneo4j-ogm/commit/73628bc82969057eea52d1e548625a2d0d418afa))


### Fix


* fix(types): Change type signature to enum ([`14a9521`](https://github.com/groc-prog/pyneo4j-ogm/commit/14a9521e502268b83fd014e1974aa56244582aa8))


* fix(types): Fix types for pattern operator ([`55a6b49`](https://github.com/groc-prog/pyneo4j-ogm/commit/55a6b494f028000a404782b1edd715b14b689096))


* fix(NodeModel): Fix invalid dict access in runtime for find_connected_nodes() method ([`7fe4efc`](https://github.com/groc-prog/pyneo4j-ogm/commit/7fe4efcc13b46d93a6a64a9cc05df72aafc035fa))


* fix: Fix typings in filters not allowing property filters ([`1f01514`](https://github.com/groc-prog/pyneo4j-ogm/commit/1f01514a19f7f95c2a581b25c4a7f7aba31f90ad))


* fix(types): Fix typings for MultiHopFilters ([`96a0a1b`](https://github.com/groc-prog/pyneo4j-ogm/commit/96a0a1bfd49d6c16a8730ff75c1edb03251dbf80))


* fix(node, relationship): Prevent adding of properties not defined on model when calling update_one or update_many ([`093ac2d`](https://github.com/groc-prog/pyneo4j-ogm/commit/093ac2ddd43979a17550c6d8db0d06d9d516f196))


* fix(node): Fix typings for auto_fetch_models parameter ([`ae247d1`](https://github.com/groc-prog/pyneo4j-ogm/commit/ae247d13d088d97ab595e5b251835c4443227444))


* fix(types): Make all query datatypes valid for $eq shorthand ([`9d4f8ed`](https://github.com/groc-prog/pyneo4j-ogm/commit/9d4f8ede91c957babb1736b72ed9a307959909d2))


* fix(types): Fix typings so the short version for {&#34;prop&#34;: {&#34;$eq&#34;: value}} is allowed ([`29b2fa4`](https://github.com/groc-prog/pyneo4j-ogm/commit/29b2fa4e488b06d570a54477034509e0a63b299d))


* fix: Fix node labels not applied to query ([`05366cc`](https://github.com/groc-prog/pyneo4j-ogm/commit/05366cc360631f63919529ee64d58a198651bcd1))


* fix: Set client builder and models properties in __init__ method ([`ab21081`](https://github.com/groc-prog/pyneo4j-ogm/commit/ab210816bf53fae7aff2c5c5056e0cf020740748))


* fix(client): Fix create_index method on client ([`8e0604b`](https://github.com/groc-prog/pyneo4j-ogm/commit/8e0604b0bc5ff9e7a0d6bcd1d4c3a90d8c17b890))


* fix(operators): Only include where queries if they are not empty strings ([`d4e74a9`](https://github.com/groc-prog/pyneo4j-ogm/commit/d4e74a9bb54e4519bd9ad0f9237aabaa0b533f78))


* fix: Fix issue where pattern operator would append [] if no node or relationship operators where passed ([`81843d9`](https://github.com/groc-prog/pyneo4j-ogm/commit/81843d9a2a207df865d46bb4aa548e30e86db960))


* fix: Fix remaining project names, fix client index creation not working if enum is passed ([`b9e08a5`](https://github.com/groc-prog/pyneo4j-ogm/commit/b9e08a5ac72ea5c931f96b05f9b1627433283012))


* fix: Fix node_match for empty labels, fix relationship_match for empty type and invalid direction ([`235574e`](https://github.com/groc-prog/pyneo4j-ogm/commit/235574e75b8fb882219c6ee1de716f0697bf3c48))


* fix: Correctly remove empty validated values ([`9053cbe`](https://github.com/groc-prog/pyneo4j-ogm/commit/9053cbe90799c651c6644485de9ae07784deb982))


* fix: Add correct typings to WithOptions method, remove useless validator from NodeModelSettings class ([`66047c6`](https://github.com/groc-prog/pyneo4j-ogm/commit/66047c6e25f60026eeb30602187afc713fbb6faa))


* fix: Fix invalid typing for all files, remove pylint from pre-commit ([`6f317e5`](https://github.com/groc-prog/pyneo4j-ogm/commit/6f317e58d2cb3e3e886da163f73df54f8b5be7bf))


* fix: Fix invalid query on create when model has no properties ([`3ebb68f`](https://github.com/groc-prog/pyneo4j-ogm/commit/3ebb68fd76955455ea560ca080b23be357464353))


* fix: Parse log level from env variable to int ([`7bf9f24`](https://github.com/groc-prog/pyneo4j-ogm/commit/7bf9f24c913cf8d59514ac36ffaac19387b95952))


* fix: Query syntax error if no relationship filters are passed ([`dbb16dc`](https://github.com/groc-prog/pyneo4j-ogm/commit/dbb16dc59b18009a702f77a00d72a6db6c119e8d))


* fix: Correctly replace relationship if allow_multiple is False and a relationship already exists ([`82a2a77`](https://github.com/groc-prog/pyneo4j-ogm/commit/82a2a77fa9d16f54612a81627a7aacb83fad157f))


* fix: Fix pylint warnings ([`7672b67`](https://github.com/groc-prog/pyneo4j-ogm/commit/7672b67ed419df3549f87f98a63ac87ce890caaf))


* fix: Make model settings available on classes instead of only instances, add typings ([`caec9b3`](https://github.com/groc-prog/pyneo4j-ogm/commit/caec9b350905745d9b497ff4e705da28a6fec564))


* fix: Set _driver to None when closing connection ([`9088cd6`](https://github.com/groc-prog/pyneo4j-ogm/commit/9088cd684cde85ce1f4016d44120fc75c830d009))


* fix: Now checking for empty WHERE statement in update_many ([`9650a89`](https://github.com/groc-prog/pyneo4j-ogm/commit/9650a89c71115ab4cb961233dd66a8b946de16b4))


* fix: Fix element_id parameter for update_one ([`e853b09`](https://github.com/groc-prog/pyneo4j-ogm/commit/e853b09f857cf7f7fdfb1dc3c4e1e446bb1d6f07))


* fix: Rename Cardinality to RelationshipPropertyCardinality, check if source node is hydrated before starting query ([`8c34e65`](https://github.com/groc-prog/pyneo4j-ogm/commit/8c34e65f7d17b41112fc5d665c51de5f2500542a))


* fix: Call .update_forward_refs() on filter validators ([`53cf0cc`](https://github.com/groc-prog/pyneo4j-ogm/commit/53cf0cc5febc12e96825fe84338c4fef584f0154))


* fix: Deflating model instance caused list items to be lost if not dict or BaseModel ([`489bc10`](https://github.com/groc-prog/pyneo4j-ogm/commit/489bc10893220591c7a1f40b2382d2fa4871c88e))


* fix: Fix validator for hook functions throwing error when something invalid is passed ([`e56ade7`](https://github.com/groc-prog/pyneo4j-ogm/commit/e56ade7cbd67a6fcd1b802e46818cefde2d222fd))


* fix: Add property getter for model settings as a dict, correctly check for missing element_id field in import_model method ([`917d07c`](https://github.com/groc-prog/pyneo4j-ogm/commit/917d07ccbe1a8e8f1370aaf525c4a9ccff326a62))


* fix: Change log format, fix env variables for logging not working ([`e6ff6a2`](https://github.com/groc-prog/pyneo4j-ogm/commit/e6ff6a260b0f9a3471393462f9e665f8abfb4c53))


* fix: Validate hooks is a list, validate settings ([`af0460f`](https://github.com/groc-prog/pyneo4j-ogm/commit/af0460f37c2d10853ab901fa053ecc06a88f4a58))


* fix: Add $neq operator to allowed operators nested inside $size ([`f5f2342`](https://github.com/groc-prog/pyneo4j-ogm/commit/f5f23424b439e56e7c542e88f793e5a29af0c769))


* fix: Fix typings and validation for $in and $nin ([`ae865ec`](https://github.com/groc-prog/pyneo4j-ogm/commit/ae865ec7f03041e513c0a9b0b780c6c081109382))


* fix: Check if predefined labels is None before trying to merge settings together ([`6b621f2`](https://github.com/groc-prog/pyneo4j-ogm/commit/6b621f289afd85d7c0cbedf8993351ee505c92d9))


* fix: Remove __settings__ from reserved property names ([`4e9a0b8`](https://github.com/groc-prog/pyneo4j-ogm/commit/4e9a0b8aaa0b976d77891afce2a34b9f5c6c9a9b))


* fix: Dont call .update in update_one to prevent multiple hooks firing ([`8396c4f`](https://github.com/groc-prog/pyneo4j-ogm/commit/8396c4f5686a7523b935d4be5823184f4b66cc48))


* fix: Add constraints to query options, include default values in validators ([`20ec7a8`](https://github.com/groc-prog/pyneo4j-ogm/commit/20ec7a8a46286e382db0fbdbc5f024fddd247d27))


* fix: Add generics to relationship property ([`3f26f2a`](https://github.com/groc-prog/pyneo4j-ogm/commit/3f26f2a9e56ee228db0dbd765af68b27af3e5225))


* fix: Correctly check if relationship is alive ([`0bfd728`](https://github.com/groc-prog/pyneo4j-ogm/commit/0bfd728a1d6ae309ed76443c58348a76dbba1c9f))


* fix: Rename arg to not shadow build in property ([`c3ae8c9`](https://github.com/groc-prog/pyneo4j-ogm/commit/c3ae8c9092f29ee1a510e9e4542fa3bc3e2e775c))


* fix: Add DISTINCT to queries to prevent duplicate results ([`4bac957`](https://github.com/groc-prog/pyneo4j-ogm/commit/4bac957b339d59fb9de75cbed79abfb45b726f7f))


* fix: Set _db_properties on instance init ([`ffe99e0`](https://github.com/groc-prog/pyneo4j-ogm/commit/ffe99e0ef49477dfda898fa80b852fbec3878ca1))


* fix: Correctly infer modified properties, now accessible with get_modified_properties property ([`56cef04`](https://github.com/groc-prog/pyneo4j-ogm/commit/56cef047063d76b72a68993dd8ca4f64f5dcf5c3))


* fix: Add hooks to create method ([`04e0bc1`](https://github.com/groc-prog/pyneo4j-ogm/commit/04e0bc14f5935754887c3afff00ef65b14455c0b))


* fix: Allow BaseModel or dict lists in models ([`c774477`](https://github.com/groc-prog/pyneo4j-ogm/commit/c7744775700a0a9984eb0ea049fff1c57831428d))


* fix: Fix different models sharing settings FOR NO FUCKING REASON AT ALL ([`898747b`](https://github.com/groc-prog/pyneo4j-ogm/commit/898747bac531793694a3974b8555417a7451fe35))


* fix: Fix hops ([`6f9eba8`](https://github.com/groc-prog/pyneo4j-ogm/commit/6f9eba8f5ac49c27e339b716ec06dc71a9e113d6))


* fix: Catch index drop errors ([`d582fe4`](https://github.com/groc-prog/pyneo4j-ogm/commit/d582fe4e989251c4ecb4840c58eb15dc09e435f2))


* fix: Fix broken query on epty filters ([`52ef2bc`](https://github.com/groc-prog/pyneo4j-ogm/commit/52ef2bcc034acc696fe76acbc0dd5af2e4c72222))


* fix: Make relationship type for multi hop relationship filters required ([`5d82f62`](https://github.com/groc-prog/pyneo4j-ogm/commit/5d82f6225d17e3b6907677ac5675c3bd04ebed86))


* fix: Make relationship type for multi hop relationship filters required ([`5830cee`](https://github.com/groc-prog/pyneo4j-ogm/commit/5830cee2b71ae566fbe6ef5c0f478e71da554e73))


* fix: Remove backticks ([`053d601`](https://github.com/groc-prog/pyneo4j-ogm/commit/053d601475c4f57ed8519d8967922fcda77678c2))


* fix: Take model settings into account before initializing model completely ([`9393058`](https://github.com/groc-prog/pyneo4j-ogm/commit/9393058708dd6068cbd1976e83a69551ed2c7612))


* fix: Remove wraps from hooks decorator ([`5ef79a3`](https://github.com/groc-prog/pyneo4j-ogm/commit/5ef79a3804a26ed9f5c9419dd9a09913e289d400))


* fix: Fix missing type hints for methods decorated by @hooks ([`07005f5`](https://github.com/groc-prog/pyneo4j-ogm/commit/07005f5155e9bf17551ce85074742e3c7c59f8e8))


* fix: Add labels where possible to relationship property query ([`abd27e2`](https://github.com/groc-prog/pyneo4j-ogm/commit/abd27e2a1d85c2999896e25aabc56c2fff55c343))


* fix: Add underscore suffix to validator field names to prevent accidental field parsing ([`217d00e`](https://github.com/groc-prog/pyneo4j-ogm/commit/217d00e9bc0b85e8dacff75eeebb59803aaf470e))


* fix: Small fixes for working methods, and for sure more come... ([`96e3a99`](https://github.com/groc-prog/pyneo4j-ogm/commit/96e3a991a80ca4710eef2280d84d0ea59b63b820))


* fix: Fix query order when no porperty to order by is defined ([`368ae7e`](https://github.com/groc-prog/pyneo4j-ogm/commit/368ae7e421af6199b3d8dabb69dee8152764867c))


* fix: Set default value for query attribute ([`c9d38c8`](https://github.com/groc-prog/pyneo4j-ogm/commit/c9d38c82622304821f393791c553540a31d95f1b))


* fix: Fix relationship property connect method not creating correct relationship match query ([`d5419f4`](https://github.com/groc-prog/pyneo4j-ogm/commit/d5419f41dbb6d73e408021a93e14b31d68bc2e32))


* fix: Fix property parameters for create method ([`9659203`](https://github.com/groc-prog/pyneo4j-ogm/commit/9659203778f7d18fc523e5be515603b6d8d74136))


* fix: Added missing $exists operator, small bug fixes ([`6fab4c7`](https://github.com/groc-prog/pyneo4j-ogm/commit/6fab4c7b9ee78ac0be89db5a4a47f2a765d8219a))


* fix: FINALLY FIX PATTERN MATCH, REMOVE RELATIONSHIP HOPS BECAUSE THEY WERE FUCKED ([`972c390`](https://github.com/groc-prog/pyneo4j-ogm/commit/972c3907e437c9f60b393f38973c52356af15610))


* fix: Update methods using query builder ([`53d5cab`](https://github.com/groc-prog/pyneo4j-ogm/commit/53d5cab2a3977bd7f1de0698eba93a3dd87f68c9))


* fix: Add pattern expression to where clause, adjust types ([`2814785`](https://github.com/groc-prog/pyneo4j-ogm/commit/2814785949e0c93862c8000fd0d9f5cd358cbe0a))


* fix: Fix None being added to match queries ([`980e690`](https://github.com/groc-prog/pyneo4j-ogm/commit/980e69030095f059d53c7108ca8b027e3ccf4335))


* fix: Replace wrong type hints for node model ([`8265c20`](https://github.com/groc-prog/pyneo4j-ogm/commit/8265c20fd526fdcf6b947fbe2958324dca203787))


* fix: Remove invalid undirected relationship direction ([`47db88f`](https://github.com/groc-prog/pyneo4j-ogm/commit/47db88f253ef659fa6e05df1e55b5ae5002eb47c))


* fix: Provide self instead of class type to _build_property method, no longer using find_one/find_many in update method ([`c007959`](https://github.com/groc-prog/pyneo4j-ogm/commit/c0079592f87dd713c30cc1ac97707f925a45ab2b))


* fix: Remove register_models_directory just because, fix model class initialization ([`1e0e68f`](https://github.com/groc-prog/pyneo4j-ogm/commit/1e0e68fbbc7fae0f4bb6a7c825c6f72050205f95))


* fix: Fix relationship model settings attribute name, fix node model labels tuple ([`6f4f02d`](https://github.com/groc-prog/pyneo4j-ogm/commit/6f4f02d34029d2cc8f1036d54fc94ab668f48596))


* fix: Fix union types for validators and TypedDict ([`8974fa0`](https://github.com/groc-prog/pyneo4j-ogm/commit/8974fa00eecc81bdf574fd9a74929e2b22514fb1))


* fix: Replace old __type__ in client ([`c555ab1`](https://github.com/groc-prog/pyneo4j-ogm/commit/c555ab18f94e530cd13290059461519cd730bba0))


* fix: Fix relationship builder breaking if no labels are provided for node ([`5028f33`](https://github.com/groc-prog/pyneo4j-ogm/commit/5028f33402c4e9c21dff09c1c20ea3a76417e44d))


* fix: Fix where clause for queries ([`a9f0501`](https://github.com/groc-prog/pyneo4j-ogm/commit/a9f05013ca91e6f531f74e4a671217bb28a1b35c))


* fix: Remove nested node patterns in favor of multiple top level node patterns ([`b0f9135`](https://github.com/groc-prog/pyneo4j-ogm/commit/b0f91353c1ec53af7c6b10ee3cff86d93f8a842e))


* fix: Updated query builder types to also include None for match and where queries ([`643c132`](https://github.com/groc-prog/pyneo4j-ogm/commit/643c13275e9b7e55e836646b22f0a19a4d8ac51a))


* fix: Fixed missing None check for query builder match query ([`a2b4ccd`](https://github.com/groc-prog/pyneo4j-ogm/commit/a2b4ccde838593e9d5a25f7e4e1d00ff8141fe12))


* fix: Remove delete_one return value since deleted nodes do not return labels, re-order validator types ([`141668b`](https://github.com/groc-prog/pyneo4j-ogm/commit/141668b709c915669a6ae96e85088222a387c81c))


* fix: Fixed find_one, update_one and deflate methods, add where in query builder return value ([`1ea505f`](https://github.com/groc-prog/pyneo4j-ogm/commit/1ea505ff3a8231e5a1451ad786e165b0ced1db75))


* fix: Add missing variable name to $exists operator ([`8ceec27`](https://github.com/groc-prog/pyneo4j-ogm/commit/8ceec27630a5913733ab65cb2013ba7d63b995b5))


* fix: Fix $in operator not working as expected, operator can now accept single value or list ([`26e7b06`](https://github.com/groc-prog/pyneo4j-ogm/commit/26e7b06aa80c2b5d56a7f820b402b770c341039b))


* fix: Correctly save dict fields to model ([`c4a4ee1`](https://github.com/groc-prog/pyneo4j-ogm/commit/c4a4ee15db2276544365d05ca1f7de79b9ed00f1))


* fix: Return self from create method so it can be chained onto init of class instance, fix error in when resolving model if query result is not a Node or Relationship instance ([`2e9df7d`](https://github.com/groc-prog/pyneo4j-ogm/commit/2e9df7d15eb3ea1eca8a2a441a8a14f26b03acd6))


* fix: Remove unused async, add type hiints for query options, fix $all operator validator to list ([`1b0a1a3`](https://github.com/groc-prog/pyneo4j-ogm/commit/1b0a1a3792ab073ab11975a6b7d969c510c616ce))


* fix: Remove model resolving where not needed ([`16228ce`](https://github.com/groc-prog/pyneo4j-ogm/commit/16228ce5c3c90b83efb5e96348091deb4fe5ca22))


* fix: Fix type in query validation, handle non dict array items ([`8a6a9fc`](https://github.com/groc-prog/pyneo4j-ogm/commit/8a6a9fc7797b425b3a3b2a2f719e487c9712e8ae))


* fix: Fix type hints ([`5850d34`](https://github.com/groc-prog/pyneo4j-ogm/commit/5850d34b7ecf8b136d9f8a68ab9ea270baf3ecb1))


* fix: Move Neo4jClient import into magic method ([`79e328a`](https://github.com/groc-prog/pyneo4j-ogm/commit/79e328a6293120612b71d757776b92ab547ccd86))


* fix: Adjust logging to correct level ([`818538d`](https://github.com/groc-prog/pyneo4j-ogm/commit/818538dc1c8efe7d64970521364c804746d0af85))


* fix: Fixed issue where $where operator was wrongfully normalized ([`7464113`](https://github.com/groc-prog/pyneo4j-ogm/commit/74641132b7f4285ffca68c61837c386a3567c3ee))


### Refactor


* refactor: Rename logging env variables ([`bdf65c8`](https://github.com/groc-prog/pyneo4j-ogm/commit/bdf65c8d8e55bf16fcdaa843aed90c7238ac7019))


* refactor: Change log level to info when falling back to class name on labels/type ([`03d37c3`](https://github.com/groc-prog/pyneo4j-ogm/commit/03d37c34c1dbc7ecc76123da0f523091a2fba51e))


* refactor: Add __eq__, __ne__, __repr__ and __str__ methods ([`7c015d3`](https://github.com/groc-prog/pyneo4j-ogm/commit/7c015d3f5b46e824592bd3417c845255bf62b0ed))


* refactor: Make element_id and id private and define setters, same for start/end node element_id and id for relationship models ([`54d5a8b`](https://github.com/groc-prog/pyneo4j-ogm/commit/54d5a8b0263dc5ede8e022677bd881baf0f6cfcf))


* refactor(node, relationship): Make inflate() and deflate() methods private ([`bbbc412`](https://github.com/groc-prog/pyneo4j-ogm/commit/bbbc41286f71e918aabb1ac59b97b04388d52b22))


* refactor: Make element_id accessible on model, change scope of some properties, tests, docs ([`071ee83`](https://github.com/groc-prog/pyneo4j-ogm/commit/071ee83bb7a3e56f8a8209da7b4dc2e668378d79))


* refactor(relationship_property): Move nodes property to top ([`3b22835`](https://github.com/groc-prog/pyneo4j-ogm/commit/3b228358ded2971df78ca6a9190204c55d3f3f00))


* refactor(client): Make methods for handling transactions protected ([`7bdab6d`](https://github.com/groc-prog/pyneo4j-ogm/commit/7bdab6d4cb46af5ce722b2908045b12aa1f68390))


* refactor: Split QueryBuilder class up and move methods which build operators to separate file ([`b67ca73`](https://github.com/groc-prog/pyneo4j-ogm/commit/b67ca73cf282b543d618040845d476357aa3c5ef))


* refactor: Move shared enums to queries.enums ([`a719b52`](https://github.com/groc-prog/pyneo4j-ogm/commit/a719b52cbcfbb5075ea575d895dd967a4ca563a1))


* refactor: Return settings model instead of dict ([`133ffe2`](https://github.com/groc-prog/pyneo4j-ogm/commit/133ffe29b236fbed707d2a6a6aef8457fa1e6b39))


* refactor: Check if models are registered only if methods on relationship properties are called ([`50b9bb5`](https://github.com/groc-prog/pyneo4j-ogm/commit/50b9bb5b1a07cfb94bef037a981a8da9cbffc533))


* refactor: Transform _ensure_alive method to decorator ([`19adea1`](https://github.com/groc-prog/pyneo4j-ogm/commit/19adea1df337a2a44bdf7a358c9a27133985b745))


* refactor: Transform _ensure_alive method to decorator ([`5fd0259`](https://github.com/groc-prog/pyneo4j-ogm/commit/5fd025980efa1119760c0d9ea4a3581c3f85ce8f))


* refactor: Transform _ensure_alive method to decorator, skip auto fetch if relationship or node model was not registered ([`46ae4e0`](https://github.com/groc-prog/pyneo4j-ogm/commit/46ae4e0fcba90f3f59d980c5fc04cd25b1f1edb2))


* refactor: Return None instead of raising an exception when no match is found for update_one() ([`eef62d1`](https://github.com/groc-prog/pyneo4j-ogm/commit/eef62d1ba9c7b70ea3beff7bb215830b4a5f4751))


* refactor: Adjust exception message ([`f3fb626`](https://github.com/groc-prog/pyneo4j-ogm/commit/f3fb626d9c03ad202e7c6f1ad23b60a746a907d0))


* refactor: Client is no longer a singleton, which allows for multiple, separate instances (can be used with threading), clients on models are now set when registering models, which makes registering models required ([`4a8d42a`](https://github.com/groc-prog/pyneo4j-ogm/commit/4a8d42a1c29b9994c6a7f105c962bf23931af14c))


* refactor: Add exports to top level __init__ file, rename node options to property options ([`a23b2ce`](https://github.com/groc-prog/pyneo4j-ogm/commit/a23b2ce5c3e1221bdee71c9c126ee62fc2acda5a))


* refactor: Make .connect method on client chainable ([`bafccdd`](https://github.com/groc-prog/pyneo4j-ogm/commit/bafccddac77aeff43189aa4be69a96ba3900ed82))


* refactor: Change back to __settings__ attribute ([`b0876c9`](https://github.com/groc-prog/pyneo4j-ogm/commit/b0876c97f6f608f22ed4d25bfba9ac1f0a38be6e))


* refactor: Rename model settings, move to property getter ([`5dde040`](https://github.com/groc-prog/pyneo4j-ogm/commit/5dde040259e8e0e7e2f075abc146c849ec3332bd))


* refactor: rename __settings to _settings ([`11cc77b`](https://github.com/groc-prog/pyneo4j-ogm/commit/11cc77bd2894e8b695a02fe39962c142bf0e363c))


* refactor: MOve __str__ to basemodel class ([`fcdc34a`](https://github.com/groc-prog/pyneo4j-ogm/commit/fcdc34ad624e687e90e2ec467044f843b803ec87))


* refactor: Remove unused settings class ([`f64c2f0`](https://github.com/groc-prog/pyneo4j-ogm/commit/f64c2f053324baa60f91050acba69eafd87da549))


* refactor: rename __model_settings__ to __settings__ ([`b516a5f`](https://github.com/groc-prog/pyneo4j-ogm/commit/b516a5fd355106a497cf5761438ae161612ac86c))


* refactor: Move ensure_alive decorator to class method, fix hooks decorator ([`aad5388`](https://github.com/groc-prog/pyneo4j-ogm/commit/aad53884bad534f6485d2bb1fedba308422385e5))


* refactor: Move pydantic settings to ModelBase ([`002796b`](https://github.com/groc-prog/pyneo4j-ogm/commit/002796b34f16c3c94018b286683a6c58f4845573))


* refactor: Rename model fields ([`7e77416`](https://github.com/groc-prog/pyneo4j-ogm/commit/7e774165a3ddd5a3a4c27c4256035e9c0e31f792))


* refactor: Unified typing style using Union instead of | ([`01bd61a`](https://github.com/groc-prog/pyneo4j-ogm/commit/01bd61a0a2f04dba0721a6a3ff1596aad738f797))


* refactor: Update RelationshipModel class to new query builder ([`dc79da4`](https://github.com/groc-prog/pyneo4j-ogm/commit/dc79da4addef9a896fdf530d0cf3da8b27c5246e))


* refactor: Adjust NodeModel class to new query builder ([`b093de5`](https://github.com/groc-prog/pyneo4j-ogm/commit/b093de5e280aac749200a4290268bbf5c74a2f1e))


* refactor: Update validators and fix convert types class to union ([`a2a62c5`](https://github.com/groc-prog/pyneo4j-ogm/commit/a2a62c53b0b35bf567f63cb695984acbe5fd526d))


* refactor: Clean up QueryBuilder class and types ([`73553aa`](https://github.com/groc-prog/pyneo4j-ogm/commit/73553aaac346e027472ab910d8a34026e44aa4ff))


* refactor: Move test files ([`0ef30e9`](https://github.com/groc-prog/pyneo4j-ogm/commit/0ef30e9b1a946407206260c1b2f9e148ea36d27a))


* refactor: Use typings types ([`5de565b`](https://github.com/groc-prog/pyneo4j-ogm/commit/5de565b7083b583e0bc0b7458dc6c185ffe796fe))


* refactor: Change _settings field to __model_settings__ ([`d7f8c3a`](https://github.com/groc-prog/pyneo4j-ogm/commit/d7f8c3aa4c835e2d3a54780b9203a2edf893397f))


* refactor: Adjust node labels casing when using class name ([`f785e29`](https://github.com/groc-prog/pyneo4j-ogm/commit/f785e29bc9ca4000f43aec7a6b5f43511591c9a9))


* refactor: Adjust labels/Type casing when using class name ([`6b0a03e`](https://github.com/groc-prog/pyneo4j-ogm/commit/6b0a03ef4c31c9888747bba1aa4ca065573378eb))


* refactor: Move RelationshipDirection enum to types ([`78c5e16`](https://github.com/groc-prog/pyneo4j-ogm/commit/78c5e16d89e02d231851013d4463c08842e48179))


* refactor: Formatting ([`519f82c`](https://github.com/groc-prog/pyneo4j-ogm/commit/519f82cf86a470a569a5e09f3309513d174faf37))


* refactor: Move labels and type to settings ([`064abde`](https://github.com/groc-prog/pyneo4j-ogm/commit/064abde111963639d8d4007e281f97620b6b5dd7))


* refactor: Remove __model_type__ and check fr issubclass ([`7a4ef01`](https://github.com/groc-prog/pyneo4j-ogm/commit/7a4ef01e4dc6e637bc6cbd44ca9805752de663e0))


* refactor: Move relationship_match method to QueryBuilder class ([`ea4c08a`](https://github.com/groc-prog/pyneo4j-ogm/commit/ea4c08a1e4e6c846c8ef1fa0cf967ff0ecbbc9ad))


* refactor: Rename NodeSchema and RelationshipSchema to NodeModel and RelationshipModel ([`26b5b95`](https://github.com/groc-prog/pyneo4j-ogm/commit/26b5b95983ff230b92dbeb6bf4d173632907e085))


* refactor: Add type hints to models registered in client, change __model_type__ from string to enum and check for valid enum member when registering model ([`3644e99`](https://github.com/groc-prog/pyneo4j-ogm/commit/3644e99d2dfeb9f7291c0184d0426a46760d1dbb))


* refactor: Move RelationshipDirection to core/relationship file ([`ab20835`](https://github.com/groc-prog/pyneo4j-ogm/commit/ab20835c0e2ed25a3d1909429481c9a83b5c2e93))


* refactor: Rename Neo4jNode to NodeSchema and Neo4jRelationship to RelationshipSchema ([`c23fd27`](https://github.com/groc-prog/pyneo4j-ogm/commit/c23fd272fe99c70d9938846a055390539076ead7))


* refactor: Move fields into separate subdir, move ensure_alive decorator into separate files and also check for start and end node id in relationship class ([`e9064c0`](https://github.com/groc-prog/pyneo4j-ogm/commit/e9064c04fce280cb1c708ff12d3b56cc53ed0e74))


* refactor: Use pattern direction for relationship class, rename to RelationshipDirection ([`41ffd61`](https://github.com/groc-prog/pyneo4j-ogm/commit/41ffd61b5161693775ceb6b3f59ba71ae3ffc5b7))


* refactor: Update relationship class methods to new query builder ([`2f0cf0d`](https://github.com/groc-prog/pyneo4j-ogm/commit/2f0cf0da95561b35db8bfc9d17b8e1ee15c10e25))


* refactor: Use typing module type hints in query builder ([`f59da73`](https://github.com/groc-prog/pyneo4j-ogm/commit/f59da73c5ad51cc5a5c302357ac4eb3a739988de))


* refactor: Update type hints to new query builder, update type hints for project to type hints from typing module ([`6e0e195`](https://github.com/groc-prog/pyneo4j-ogm/commit/6e0e19528a74d47a41e0a0802cc1d869f054a719))


* refactor: Refactor node methods for new query builder ([`f460b87`](https://github.com/groc-prog/pyneo4j-ogm/commit/f460b874a3baf0e65290d96b2319cc261482cd5a))


* refactor: Renamed query builder method ([`5d7a27d`](https://github.com/groc-prog/pyneo4j-ogm/commit/5d7a27dca697fdfc93ca5f05fe2018ac178ad831))


* refactor: Explicitly manage transactions ([`0417f25`](https://github.com/groc-prog/pyneo4j-ogm/commit/0417f2512aeee890c16b334972f92e19eab8ca30))


* refactor: Move node and client to core directory ([`e5a7d69`](https://github.com/groc-prog/pyneo4j-ogm/commit/e5a7d698f2e0d397e748b472c013a735bef01f4b))


* refactor: Move node and client to core directory ([`1a6b61f`](https://github.com/groc-prog/pyneo4j-ogm/commit/1a6b61fbc4a6405ed37ec3dedfb8d41cfe54c483))


* refactor: Renamed method, small docs change ([`89306d7`](https://github.com/groc-prog/pyneo4j-ogm/commit/89306d730923a76f380a0f9cc47ba8fe9eb052f1))


* refactor(OperantQueryBuilder): Normalize query before working with it ([`fde67bb`](https://github.com/groc-prog/pyneo4j-ogm/commit/fde67bb7b333abd8710a011281f2b02da4468859))


* refactor: Adjust variable names in QueryBuilder ([`c7bbdaa`](https://github.com/groc-prog/pyneo4j-ogm/commit/c7bbdaa797f588b2b1446d102f8f47e972cdc25a))


* refactor: Renamed property_filters file to query_builder ([`18eb26a`](https://github.com/groc-prog/pyneo4j-ogm/commit/18eb26a4389700247f92b1e34d9af8eff677ac82))


* refactor: Move files to package level ([`2667f20`](https://github.com/groc-prog/pyneo4j-ogm/commit/2667f20bcf5ec0609809363167130df46abc5373))


* refactor: Moved direction enum to utils ([`482506a`](https://github.com/groc-prog/pyneo4j-ogm/commit/482506aca2136a227c566678a34c0e98a7c86bc2))


