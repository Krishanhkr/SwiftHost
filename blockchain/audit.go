package main

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// SmartContract provides functions for managing audit logs
type SmartContract struct {
	contractapi.Contract
}

// AccessLog represents an audit log entry
type AccessLog struct {
	User      string `json:"user"`
	Resource  string `json:"resource"`
	Timestamp int64  `json:"timestamp"`
	TxID      string `json:"txid"`
}

// InitLedger adds a base set of audit logs to the ledger
func (s *SmartContract) InitLedger(ctx contractapi.TransactionContextInterface) error {
	logs := []AccessLog{
		{User: "admin", Resource: "system", Timestamp: time.Now().Unix(), TxID: ctx.GetStub().GetTxID()},
	}
	
	for i, log := range logs {
		logAsBytes, _ := json.Marshal(log)
		err := ctx.GetStub().PutState(fmt.Sprintf("LOG-%d", i), logAsBytes)
		if err != nil {
			return fmt.Errorf("Failed to put to world state. %s", err.Error())
		}
	}
	
	return nil
}

// LogAccess creates a new audit log on the ledger
func (s *SmartContract) LogAccess(ctx contractapi.TransactionContextInterface, userId, resource string) error {
	timestamp := time.Now().Unix()
	log := AccessLog{
		User:      userId,
		Resource:  resource,
		Timestamp: timestamp,
		TxID:      ctx.GetStub().GetTxID(),
	}
	
	logBytes, _ := json.Marshal(log)
	return ctx.GetStub().PutState(fmt.Sprintf("LOG-%s-%d", userId, timestamp), logBytes)
}

// GetAllLogs returns all audit logs found in world state
func (s *SmartContract) GetAllLogs(ctx contractapi.TransactionContextInterface) ([]*AccessLog, error) {
	// Range query with empty string for startKey and endKey does an open-ended query of all logs in the chaincode namespace
	resultsIterator, err := ctx.GetStub().GetStateByRange("", "")
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()
	
	var logs []*AccessLog
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}
		
		var log AccessLog
		err = json.Unmarshal(queryResponse.Value, &log)
		if err != nil {
			return nil, err
		}
		logs = append(logs, &log)
	}
	
	return logs, nil
}

func main() {
	auditChaincode, err := contractapi.NewChaincode(&SmartContract{})
	if err != nil {
		fmt.Printf("Error creating audit-trail chaincode: %s", err.Error())
		return
	}
	
	if err := auditChaincode.Start(); err != nil {
		fmt.Printf("Error starting audit-trail chaincode: %s", err.Error())
	}
} 