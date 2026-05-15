declare module "react-scrollama" {
  import { ReactNode } from "react";
  export interface CallbackResponse<T = unknown> {
    data: T;
    direction: "up" | "down";
    element: HTMLElement;
    entry: IntersectionObserverEntry;
  }
  export interface ScrollamaProps {
    offset?: number;
    threshold?: number;
    debug?: boolean;
    onStepEnter?: (resp: CallbackResponse) => void;
    onStepExit?: (resp: CallbackResponse) => void;
    onStepProgress?: (resp: CallbackResponse & { progress: number }) => void;
    children?: ReactNode;
  }
  export const Scrollama: React.FC<ScrollamaProps>;
  export interface StepProps {
    data?: unknown;
    children?: ReactNode;
  }
  export const Step: React.FC<StepProps>;
}
