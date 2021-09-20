# from system.utils import *
# from indy import pool, did, payment
# import pytest
# import asyncio


# @pytest.mark.skip(reason='ST-580')
# @pytest.mark.asyncio
# async def test_libsovtoken_acceptance(docker_setup_and_teardown):
#     await pool.set_protocol_version(2)
#     await payment_initializer('libsovtoken.so', 'sovtoken_init')
#     # await payment_initializer('libnullpay.so', 'nullpay_init')
#     pool_handle, _ = await pool_helper()
#     wallet_handle, _, _ = await wallet_helper()
#     libsovtoken_payment_method = 'sov'
#     libnullpay_payment_method = 'null'

#     trustee_did1, trustee_vk1 = await did.create_and_store_my_did(wallet_handle, json.dumps(
#         {"seed": str('000000000000000000000000Trustee1')}))
#     trustee_did2, trustee_vk2 = await did.create_and_store_my_did(wallet_handle, json.dumps(
#         {"seed": str('000000000000000000000000Trustee2')}))
#     trustee_did3, trustee_vk3 = await did.create_and_store_my_did(wallet_handle, json.dumps(
#         {"seed": str('000000000000000000000000Trustee3')}))
#     trustee_did4, trustee_vk4 = await did.create_and_store_my_did(wallet_handle, json.dumps(
#         {"seed": str('000000000000000000000000Trustee4')}))

#     await send_nym(pool_handle, wallet_handle, trustee_did1, trustee_did2, trustee_vk2, None, 'TRUSTEE')
#     await send_nym(pool_handle, wallet_handle, trustee_did1, trustee_did3, trustee_vk3, None, 'TRUSTEE')
#     await send_nym(pool_handle, wallet_handle, trustee_did1, trustee_did4, trustee_vk4, None, 'TRUSTEE')

#     fees = {'1': 1, '100': 1, '101': 1, '102': 1, '113': 1, '114': 1, '10001': 1}
#     req = await payment.build_set_txn_fees_req(wallet_handle, trustee_did1, libsovtoken_payment_method,
#                                                json.dumps(fees))

#     req = await ledger.multi_sign_request(wallet_handle, trustee_did1, req)
#     req = await ledger.multi_sign_request(wallet_handle, trustee_did2, req)
#     req = await ledger.multi_sign_request(wallet_handle, trustee_did3, req)
#     req = await ledger.multi_sign_request(wallet_handle, trustee_did4, req)

#     res2 = json.loads(await ledger.submit_request(pool_handle, req))
#     print(res2)
#     assert res2['op'] == 'REPLY'

#     req = await payment.build_get_txn_fees_req(wallet_handle, trustee_did1, libsovtoken_payment_method)
#     res3 = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did1, req))
#     assert res3['result']['fees'] == fees

#     address1 = await payment.create_payment_address(wallet_handle, libsovtoken_payment_method, json.dumps(
#         {"seed": str('0000000000000000000000000Wallet3')}))
#     address2 = await payment.create_payment_address(wallet_handle, libsovtoken_payment_method, json.dumps(
#         {"seed": str('0000000000000000000000000Wallet4')}))
#     address3 = await payment.create_payment_address(wallet_handle, libsovtoken_payment_method, json.dumps(
#         {"seed": str('0000000000000000000000000Wallet5')}))
#     address4 = await payment.create_payment_address(wallet_handle, libsovtoken_payment_method, json.dumps(
#         {"seed": str('0000000000000000000000000Wallet6')}))
#     address5 = await payment.create_payment_address(wallet_handle, libsovtoken_payment_method, json.dumps(
#         {"seed": str('0000000000000000000000000Wallet7')}))

#     map1 = {"recipient": address1, "amount": 5}
#     map2 = {"recipient": address2, "amount": 1}
#     map3 = {"recipient": address3, "amount": 1}
#     map4 = {"recipient": address4, "amount": 4}
#     map5 = {"recipient": address5, "amount": 1}
#     list1 = [map1, map2, map3, map4, map5]
#     req, _ = await payment.build_mint_req(wallet_handle, trustee_did1,
#                                           json.dumps(list1), None)

#     req = await ledger.multi_sign_request(wallet_handle, trustee_did1, req)
#     req = await ledger.multi_sign_request(wallet_handle, trustee_did2, req)
#     req = await ledger.multi_sign_request(wallet_handle, trustee_did3, req)
#     req = await ledger.multi_sign_request(wallet_handle, trustee_did4, req)

#     res0 = json.loads(await ledger.submit_request(pool_handle, req))
#     print('MINT RESULT: {}'.format(res0))
#     assert res0['op'] == 'REPLY'

#     req, _ = await payment.build_get_payment_sources_request(wallet_handle, trustee_did1, address1)
#     res1 = await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did1, req)
#     source1 = await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res1)
#     source1 = json.loads(source1)[0]['source']
#     l1 = [source1]

#     req, _ = await payment.build_get_payment_sources_request(wallet_handle, trustee_did1, address2)
#     res2 = await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did1, req)
#     source2 = await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res2)
#     source2 = json.loads(source2)[0]['source']
#     l2 = [source2]

#     req, _ = await payment.build_get_payment_sources_request(wallet_handle, trustee_did1, address3)
#     res3 = await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did1, req)
#     source3 = await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res3)
#     source3 = json.loads(source3)[0]['source']
#     l3 = [source3]

#     req, _ = await payment.build_get_payment_sources_request(wallet_handle, trustee_did1, address4)
#     res4 = await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did1, req)
#     source4 = await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res4)
#     source4 = json.loads(source4)[0]['source']
#     l4 = [source4]

#     req, _ = await payment.build_get_payment_sources_request(wallet_handle, trustee_did1, address5)
#     res5 = await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did1, req)
#     source5 = await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res5)
#     source5 = json.loads(source5)[0]['source']
#     l5 = [source5]

#     # send schema, no tokens
#     _, res = await send_schema(pool_handle, wallet_handle, trustee_did1, random_string(5), '1.0',
#                                json.dumps(["name", "age"]))
#     assert res['op'] == 'REJECT'

#     # send schema, enough tokens
#     schema_id, schema_json = \
#         await anoncreds.issuer_create_schema(trustee_did1, random_string(5), '1.0', json.dumps(["name", "age"]))
#     req = await ledger.build_schema_request(trustee_did1, schema_json)
#     req_with_fees_json, _ = await payment.add_request_fees(wallet_handle, trustee_did1, req, json.dumps(l2), '[]', None)
#     res5 = json.loads(
#         await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did1, req_with_fees_json))
#     assert res5['op'] == 'REPLY'

#     # get schema
#     await asyncio.sleep(1)
#     res6 = await get_schema(pool_handle, wallet_handle, trustee_did1, schema_id)
#     assert res6['result']['seqNo'] is not None
#     schema_id, schema_json = await ledger.parse_get_schema_response(json.dumps(res6))

#     cred_def_id, cred_def_json = \
#         await anoncreds.issuer_create_and_store_credential_def(wallet_handle, trustee_did1, schema_json,
#                                                                random_string(5), 'CL',
#                                                                json.dumps({'support_revocation': False}))
#     # cred_def incorrect
#     req = await ledger.build_cred_def_request(trustee_did1, cred_def_json)
#     req_with_fees_json1, _ =\
#         await payment.add_request_fees(wallet_handle, trustee_did1, req, json.dumps(l3), '[]', None)
#     res7 = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did1, req))
#     assert res7['op'] == 'REJECT'

#     # cred_def correct
#     req = await ledger.build_cred_def_request(trustee_did1, cred_def_json)
#     req_with_fees_json2, _ =\
#         await payment.add_request_fees(wallet_handle, trustee_did1, req, json.dumps(l5), '[]', None)
#     res8 = json.loads(
#         await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did1, req_with_fees_json2))
#     assert res8['op'] == 'REPLY'

#     # get cred def
#     res9 = await get_cred_def(pool_handle, wallet_handle, trustee_did1, cred_def_id)
#     assert res9['result']['seqNo'] is not None

#     # send nym with fees
#     map8 = {"recipient": address1, "amount": 3}
#     l8 = [map8]
#     req = await ledger.build_nym_request(trustee_did1, 'V4SGRU86Z58d6TV7PBU111', None, None, None)
#     req_with_fees_json, _ = await payment.add_request_fees(wallet_handle, trustee_did1, req, json.dumps(l4),
#                                                            json.dumps(l8), None)
#     res10 = json.loads(
#         await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did1, req_with_fees_json))
#     assert res10['op'] == 'REPLY'

#     # rotate key with fees
#     map9 = {"recipient": address1, "amount": 4}
#     l9 = [map9]
#     res11 = await did.key_for_local_did(wallet_handle, trustee_did2)
#     new_key = await did.replace_keys_start(wallet_handle, trustee_did2, json.dumps({}))
#     req = await ledger.build_nym_request(trustee_did2, trustee_did2, new_key, None, None)
#     req_with_fees_json, _ = await payment.add_request_fees(wallet_handle, trustee_did2, req, json.dumps(l1),
#                                                            json.dumps(l9), None)
#     res_ = json.loads(
#         await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did2, req_with_fees_json))
#     assert res_['op'] == 'REPLY'
#     res__ = await did.replace_keys_apply(wallet_handle, trustee_did2)
#     assert res__ is None
#     res12 = await did.key_for_local_did(wallet_handle, trustee_did2)
#     assert res12 != res11
#     assert res12 == new_key
