// Excel's script editor provides this namespace globally. Local tsc uses the
// unmodified Microsoft declaration file through this type-only bridge.
import { ExcelScript as API } from './excelscript';
declare global {
  namespace ExcelScript {
    type Workbook = API.Workbook;
  }
}
