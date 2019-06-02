extern crate indyrs as indy;
extern crate futures;

use indy::pool;
use indy::wallet;
#[allow(unused_imports)]
use futures::Future;


#[test]
pub fn test_misc(){
    indy::pool::set_protocol_version(2).wait();

    let p_name = "pool_name";
    let p_config = r#"{"genesis_txn":"../docker_genesis"}"#;
    let _pool = indy::pool::create_pool_ledger_config(&p_name, Some(&p_config)).wait();
    let p_handle = indy::pool::open_pool_ledger(&p_name, None).wait().unwrap();
    println!("POOL HANDLE >>> {}", p_handle);

    let w_config = r#"{"id":"id"}"#;
    let w_credentials = r#"{"key":"key"}"#;
    let _wallet = indy::wallet::create_wallet(&w_config, &w_credentials).wait();
    let w_handle = indy::wallet::open_wallet(&w_config, &w_credentials).wait().unwrap();
    println!("WALLET HANDLE >>> {}", w_handle);

    // TODO play with proptest

    assert!(true);
}