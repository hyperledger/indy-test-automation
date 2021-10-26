# import pytest
# import asyncio
# from system.utils import *
# from indy import payment


# import logging
# logger = logging.getLogger(__name__)


# @pytest.mark.usefixtures('docker_setup_and_teardown')
# @pytest.mark.usefixtures('payment_init')
# class TestAuthMapPluginsSuite:
#     @pytest.mark.parametrize('adder_role, adder_role_num', [
#         ('TRUSTEE', '0'),
#         ('STEWARD', '2'),
#         ('TRUST_ANCHOR', '101'),
#         ('NETWORK_MONITOR', '201')
#     ])
#     @pytest.mark.parametrize('sig_count', [0, 1, 3])
#     @pytest.mark.asyncio
#     async def test_case_mint(
#             self, pool_handler, wallet_handler, get_default_trustee, adder_role, adder_role_num, sig_count
#     ):
#         libsovtoken_payment_method = 'sov'
#         trustee_did, _ = get_default_trustee
#         address = await payment.create_payment_address(
#             wallet_handler, libsovtoken_payment_method, json.dumps({"seed": str('0000000000000000000000000Wallet0')})
#         )
#         # set rule for adding
#         req = await ledger.build_auth_rule_request(trustee_did, '10000', 'ADD', '*', '*', '*',
#                                                    json.dumps({
#                                                        'constraint_id': 'ROLE',
#                                                        'role': adder_role_num,
#                                                        'sig_count': sig_count,
#                                                        'need_to_be_owner': False,
#                                                        'metadata': {}
#                                                    }))
#         res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
#         print(res2)
#         assert res2['op'] == 'REPLY'
#         if sig_count == 0:
#             # add identity owner adder to mint tokens
#             adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
#             res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, None)
#             assert res['op'] == 'REPLY'
#             req, _ = await payment.build_mint_req(
#                 wallet_handler, adder_did, json.dumps([{"recipient": address, "amount": 100}]), None
#             )
#             res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, req))
#             print(res1)
#             assert res1['op'] == 'REPLY'
#         elif sig_count == 1:
#             # add adder to mint tokens
#             adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
#             res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
#             assert res['op'] == 'REPLY'
#             req, _ = await payment.build_mint_req(
#                 wallet_handler, adder_did, json.dumps([{"recipient": address, "amount": 100}]), None
#             )
#             res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, req))
#             print(res1)
#             assert res1['op'] == 'REPLY'
#         else:
#             # add adders to mint tokens
#             adder_did1, adder_vk1 = await did.create_and_store_my_did(wallet_handler, '{}')
#             res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did1, adder_vk1, None, adder_role)
#             assert res['op'] == 'REPLY'
#             adder_did2, adder_vk2 = await did.create_and_store_my_did(wallet_handler, '{}')
#             res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did2, adder_vk2, None, adder_role)
#             assert res['op'] == 'REPLY'
#             adder_did3, adder_vk3 = await did.create_and_store_my_did(wallet_handler, '{}')
#             res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did3, adder_vk3, None, adder_role)
#             assert res['op'] == 'REPLY'
#             req, _ = await payment.build_mint_req(
#                 wallet_handler, adder_did1, json.dumps([{"recipient": address, "amount": 100}]), None
#             )
#             req = await ledger.multi_sign_request(wallet_handler, adder_did1, req)
#             req = await ledger.multi_sign_request(wallet_handler, adder_did2, req)
#             req = await ledger.multi_sign_request(wallet_handler, adder_did3, req)
#             res1 = json.loads(await ledger.submit_request(pool_handler, req))
#             print(res1)
#             assert res1['op'] == 'REPLY'

#     @pytest.mark.parametrize('editor_role, editor_role_num', [
#         ('NETWORK_MONITOR', '201'),
#         ('TRUST_ANCHOR', '101'),
#         ('STEWARD', '2'),
#         ('TRUSTEE', '0')
#     ])
#     @pytest.mark.parametrize('sig_count', [0, 1, 3])
#     @pytest.mark.asyncio
#     async def test_case_set_fees(
#             self, pool_handler, wallet_handler, get_default_trustee,
#             editor_role, editor_role_num, sig_count
#     ):
#         libsovtoken_payment_method = 'sov'
#         fees = {'1': 1, '100': 1, '101': 1, '102': 1, '113': 1, '114': 1, '10001': 1}
#         trustee_did, _ = get_default_trustee
#         # set rule for adding
#         req = await ledger.build_auth_rule_request(trustee_did, '20000', 'EDIT', '*', '*', '*',
#                                                    json.dumps({
#                                                        'constraint_id': 'ROLE',
#                                                        'role': editor_role_num,
#                                                        'sig_count': sig_count,
#                                                        'need_to_be_owner': False,
#                                                        'metadata': {}
#                                                    }))
#         res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
#         print(res2)
#         assert res2['op'] == 'REPLY'
#         if sig_count == 0:
#             # add identity owner editor to set fees
#             editor_did, editor_vk = await did.create_and_store_my_did(wallet_handler, '{}')
#             res = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did, editor_vk, None, None)
#             assert res['op'] == 'REPLY'
#             req = await payment.build_set_txn_fees_req(
#                 wallet_handler, editor_did, libsovtoken_payment_method, json.dumps(fees)
#             )
#             res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, editor_did, req))
#             print(res1)
#             assert res1['op'] == 'REPLY'
#         elif sig_count == 1:
#             # add editor to set fees
#             editor_did, editor_vk = await did.create_and_store_my_did(wallet_handler, '{}')
#             res = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did, editor_vk, None, editor_role)
#             assert res['op'] == 'REPLY'
#             req = await payment.build_set_txn_fees_req(
#                 wallet_handler, editor_did, libsovtoken_payment_method, json.dumps(fees)
#             )
#             res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, editor_did, req))
#             print(res1)
#             assert res1['op'] == 'REPLY'
#         else:
#             # add editors to set fees
#             editor_did1, editor_vk1 = await did.create_and_store_my_did(wallet_handler, '{}')
#             res = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did1, editor_vk1, None, editor_role)
#             assert res['op'] == 'REPLY'
#             editor_did2, editor_vk2 = await did.create_and_store_my_did(wallet_handler, '{}')
#             res = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did2, editor_vk2, None, editor_role)
#             assert res['op'] == 'REPLY'
#             editor_did3, editor_vk3 = await did.create_and_store_my_did(wallet_handler, '{}')
#             res = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did3, editor_vk3, None, editor_role)
#             assert res['op'] == 'REPLY'
#             req = await payment.build_set_txn_fees_req(
#                 wallet_handler, editor_did1, libsovtoken_payment_method, json.dumps(fees)
#             )
#             req = await ledger.multi_sign_request(wallet_handler, editor_did1, req)
#             req = await ledger.multi_sign_request(wallet_handler, editor_did2, req)
#             req = await ledger.multi_sign_request(wallet_handler, editor_did3, req)
#             res1 = json.loads(await ledger.submit_request(pool_handler, req))
#             print(res1)
#             assert res1['op'] == 'REPLY'

#     @pytest.mark.parametrize('adder_role, adder_role_num', [
#         ('TRUSTEE', '0'),
#         ('STEWARD', '2'),
#         ('TRUST_ANCHOR', '101'),
#         ('NETWORK_MONITOR', '201')
#     ])
#     @pytest.mark.parametrize('sig_count', [0, 1, 3])
#     @pytest.mark.asyncio
#     async def test_case_payment(
#             self, pool_handler, wallet_handler, get_default_trustee, adder_role, adder_role_num, sig_count
#     ):
#         libsovtoken_payment_method = 'sov'
#         trustee_did, _ = get_default_trustee
#         address1 = await payment.create_payment_address(
#             wallet_handler, libsovtoken_payment_method, json.dumps({"seed": str('0000000000000000000000000Wallet1')})
#         )
#         address2 = await payment.create_payment_address(
#             wallet_handler, libsovtoken_payment_method, json.dumps({"seed": str('0000000000000000000000000Wallet2')})
#         )
#         # set rule for easier mint adding
#         req = await ledger.build_auth_rule_request(trustee_did, '10000', 'ADD', '*', '*', '*',
#                                                    json.dumps({
#                                                        'constraint_id': 'ROLE',
#                                                        'role': '*',
#                                                        'sig_count': 1,
#                                                        'need_to_be_owner': False,
#                                                        'metadata': {}
#                                                    }))
#         res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
#         print(res1)
#         assert res1['op'] == 'REPLY'
#         # set rule for adding
#         req = await ledger.build_auth_rule_request(trustee_did, '10001', 'ADD', '*', '*', '*',
#                                                    json.dumps({
#                                                        'constraint_id': 'ROLE',
#                                                        'role': adder_role_num,
#                                                        'sig_count': sig_count,
#                                                        'need_to_be_owner': False,
#                                                        'metadata': {}
#                                                    }))
#         res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
#         print(res2)
#         assert res2['op'] == 'REPLY'
#         # initial minting
#         req, _ = await payment.build_mint_req(
#             wallet_handler, trustee_did, json.dumps([{"recipient": address1, "amount": 100}]), None
#         )
#         res11 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
#         print(res11)
#         assert res11['op'] == 'REPLY'
#         req, _ = await payment.build_get_payment_sources_request(wallet_handler, trustee_did, address1)
#         res111 = await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
#         source1 = json.loads(
#             await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res111)
#         )[0]['source']
#         if sig_count == 0:
#             # add identity owner adder to send xfer
#             adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
#             res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, None)
#             assert res['op'] == 'REPLY'
#             req, _ = await payment.build_payment_req(
#                 wallet_handler, adder_did, json.dumps([source1]), json.dumps([{"recipient": address2, "amount": 100}]),
#                 None
#             )
#             res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, req))
#             print(res1)
#             assert res1['op'] == 'REPLY'
#         elif sig_count == 1:
#             # add adder to send xfer
#             adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
#             res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
#             assert res['op'] == 'REPLY'
#             req, _ = await payment.build_payment_req(
#                 wallet_handler, adder_did, json.dumps([source1]), json.dumps([{"recipient": address2, "amount": 100}]),
#                 None
#             )
#             res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, req))
#             print(res1)
#             assert res1['op'] == 'REPLY'
#         else:
#             # add adders to send xfer
#             adder_did1, adder_vk1 = await did.create_and_store_my_did(wallet_handler, '{}')
#             res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did1, adder_vk1, None, adder_role)
#             assert res['op'] == 'REPLY'
#             adder_did2, adder_vk2 = await did.create_and_store_my_did(wallet_handler, '{}')
#             res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did2, adder_vk2, None, adder_role)
#             assert res['op'] == 'REPLY'
#             adder_did3, adder_vk3 = await did.create_and_store_my_did(wallet_handler, '{}')
#             res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did3, adder_vk3, None, adder_role)
#             assert res['op'] == 'REPLY'
#             req, _ = await payment.build_payment_req(
#                 wallet_handler, adder_did1, json.dumps([source1]), json.dumps([{"recipient": address2, "amount": 100}]),
#                 None
#             )
#             req = await ledger.multi_sign_request(wallet_handler, adder_did1, req)
#             req = await ledger.multi_sign_request(wallet_handler, adder_did2, req)
#             req = await ledger.multi_sign_request(wallet_handler, adder_did3, req)
#             res1 = json.loads(await ledger.submit_request(pool_handler, req))
#             print(res1)
#             assert res1['op'] == 'REPLY'
