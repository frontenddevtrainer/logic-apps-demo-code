# Day 9: Error Handling, Logging, and Best Practices

**Duration:** 2 hours

## Learning objectives
1. Implement practical error handling with try/catch scopes in Logic Apps.
2. Set up Application Insights for monitoring and logging.
3. Apply best practices for organizing and naming workflows.

## Examples and code walkthroughs
- **Try/Catch/Finally** pattern using Logic App **Scope** actions.
- **Application Insights query**:
  ```kusto
  traces
  | where message contains "error"
  | order by timestamp desc
  ```
- **Naming conventions**:
  - Logic Apps: `LA-ProjectName-WorkflowName`
  - Functions: `FA-ProjectName-FunctionName`

## Live demos
1. **Demo 1**: Adding Scope actions for error handling in Logic Apps
   - `Day 9/Demo 1/README.md`
2. **Demo 2**: Configuring Application Insights for Logic Apps and Functions
   - `Day 9/Demo 2/README.md`
3. **Demo 3**: Creating custom logging with trackEvent and trackException
   - `Day 9/Demo 3/README.md`
4. **Demo 4**: Building a simple monitoring dashboard in Azure Portal
   - `Day 9/Demo 4/README.md`

## Hands-on lab
Enhance a Logic App workflow with proper error handling:
1. Wrap main logic in a Scope action.
2. Add a catch scope that logs errors to Application Insights.
3. Send email notification on failure.
4. Add custom tracking properties for debugging.
5. Create a simple KQL query to find recent errors.

Lab guide and code:
- `Day 9/Hands On/README.md`
- `Day 9/Hands On/error-handling-hands-on/ErrorHandlingLab/workflow.json`
