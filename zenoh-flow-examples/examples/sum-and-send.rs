//
// Copyright (c) 2017, 2021 ADLINK Technology Inc.
//
// This program and the accompanying materials are made available under the
// terms of the Eclipse Public License 2.0 which is available at
// http://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0
// which is available at https://www.apache.org/licenses/LICENSE-2.0.
//
// SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
//
// Contributors:
//   ADLINK zenoh team, <zenoh@adlink-labs.tech>
//

use async_std::sync::Arc;
use std::collections::HashMap;
use zenoh_flow::zenoh_flow_derive::ZFState;
use zenoh_flow::PortId;
use zenoh_flow::{
    default_input_rule, default_output_rule, downcast_mut, get_input, zf_data, Component,
    DataTrait, StateTrait, ZFComponentInputRule, ZFComponentOutput, ZFComponentOutputRule,
    ZFOperatorTrait, ZFResult,
};
use zenoh_flow_examples::ZFUsize;

#[derive(Debug)]
struct SumAndSend;

#[derive(Debug, Clone, ZFState)]
struct SumAndSendState {
    pub x: ZFUsize,
}

static INPUT: &str = "Number";
static OUTPUT: &str = "Sum";

impl ZFOperatorTrait for SumAndSend {
    fn run(
        &self,
        _context: &mut zenoh_flow::Context,
        dyn_state: &mut Box<dyn zenoh_flow::StateTrait>,
        inputs: &mut HashMap<PortId, zenoh_flow::runtime::message::ZFDataMessage>,
    ) -> zenoh_flow::ZFResult<HashMap<zenoh_flow::PortId, Arc<dyn DataTrait>>> {
        let mut results: HashMap<PortId, Arc<dyn DataTrait>> = HashMap::new();

        // Downcasting state to right type
        let mut state = downcast_mut!(SumAndSendState, dyn_state).unwrap();

        let (_, data) = get_input!(ZFUsize, String::from(INPUT), inputs)?;

        let res = ZFUsize(state.x.0 + data.0);
        state.x = res.clone();

        results.insert(OUTPUT.into(), zf_data!(res));
        Ok(results)
    }
}

impl ZFComponentInputRule for SumAndSend {
    fn input_rule(
        &self,
        _context: &mut zenoh_flow::Context,
        state: &mut Box<dyn zenoh_flow::StateTrait>,
        tokens: &mut HashMap<PortId, zenoh_flow::Token>,
    ) -> zenoh_flow::ZFResult<bool> {
        default_input_rule(state, tokens)
    }
}

impl ZFComponentOutputRule for SumAndSend {
    fn output_rule(
        &self,
        _context: &mut zenoh_flow::Context,
        state: &mut Box<dyn zenoh_flow::StateTrait>,
        outputs: &HashMap<PortId, Arc<dyn DataTrait>>,
    ) -> zenoh_flow::ZFResult<HashMap<zenoh_flow::PortId, ZFComponentOutput>> {
        default_output_rule(state, outputs)
    }
}

impl Component for SumAndSend {
    fn initialize(
        &self,
        _configuration: &Option<HashMap<String, String>>,
    ) -> Box<dyn zenoh_flow::StateTrait> {
        Box::new(SumAndSendState { x: ZFUsize(0) })
    }

    fn clean(&self, _state: &mut Box<dyn StateTrait>) -> ZFResult<()> {
        Ok(())
    }
}

// Also generated by macro
zenoh_flow::export_operator!(register);

fn register() -> ZFResult<Arc<dyn ZFOperatorTrait>> {
    Ok(Arc::new(SumAndSend) as Arc<dyn ZFOperatorTrait>)
}
