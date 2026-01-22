curl -s "http://localhost:7071/runtime/webhooks/workflow/api/management/workflows/FinalProject/triggers?api-version=2020-05-01-preview"


curl -s "http://localhost:7071/runtime/webhooks/workflow/api/management/workflows/FinalProject/runs?api-version=2020-05-01-preview"


curl -X POST "http://localhost:7071/runtime/webhooks/workflow/api/management/workflows/FinalProject/triggers/HTTP_Request_-_Receive_X12_Order/run?api-version=2020-05-01-preview" \
  -H "Content-Type: application/json" \
  -d '{
    "x12": "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *230101*1200*U*00401*000000001*0*P*>~GS*PO*SENDER*RECEIVER*20230101*1200*1*X*004010~ST*850*0001~BEG*00*SA*PO123456**20230101~PO1*1*10*EA*25.00**VP*WIDGET-001~CTT*1~SE*5*0001~GE*1*1~IEA*1*000000001~",
    "client": "default"
  }'



  curl -X POST "http://localhost:7071/runtime/webhooks/workflow/api/management/workflows/FinalProject/triggers/HTTP_Request_-_Receive_X12_Order/run?api-version=2020-05-01-preview" \
  -H "Content-Type: application/json" \
  -d '{
    "x12": "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *230101*1200*U*00401*000000001*0*P*>~GS*PO*SENDER*RECEIVER*20230101*1200*1*X*004010~ST*850*0001~BEG*00*SA*PO123456**20230101~PO1*1*10*EA*25.00**VP*WIDGET-001~CTT*1~SE*5*0001~GE*1*1~IEA*1*000000001~",
    "client": "default"
  }'

  Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw