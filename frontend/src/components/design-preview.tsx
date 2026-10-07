"use client";
import { useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import * as Toast from "@radix-ui/react-toast";
import * as Select from "@radix-ui/react-select";
import * as Checkbox from "@radix-ui/react-checkbox";
import { Check, ChevronDown, Ticket, X } from "lucide-react";
import { Badge, Button, Card, Pill, Skeleton, Stepper } from "./ui";

const swatches = [
  "brand-500",
  "brand-700",
  "brand-100",
  "brand-50",
  "ink",
  "muted",
  "success",
  "warning",
  "danger",
  "highlight",
];
export function DesignPreview() {
  const [quantity, setQuantity] = useState(1);
  const [toast, setToast] = useState(false);
  const [category, setCategory] = useState("music");
  const [accepted, setAccepted] = useState(false);
  return (
    <Toast.Provider duration={4500}>
      <div className="design-grid">
        <Card className="design-section">
          <h2>The palette.</h2>
          <div className="swatches">
            {swatches.map((color) => (
              <div className="swatch" key={color}>
                <i style={{ background: `var(--${color})` }} />
                <span>{color}</span>
              </div>
            ))}
          </div>
        </Card>
        <Card className="design-section">
          <h2>
            A little <em>character.</em>
          </h2>
          <p className="muted">
            Playfair Display adds the feeling. Inter keeps everything clear.
            JetBrains Mono gives the details their own rhythm.
          </p>
          <div className="component-row">
            <Pill>01 · THE SMALL DETAILS</Pill>
          </div>
          <p className="mono">BDT 1,200 · DHAKA, BANGLADESH</p>
        </Card>
        <Card className="design-section">
          <h2>Make a move.</h2>
          <div className="component-row">
            <Button onClick={() => setToast(true)}>Primary action</Button>
            <Button variant="secondary" onClick={() => setToast(true)}>
              Secondary
            </Button>
            <Button variant="danger" onClick={() => setToast(true)}>
              Destructive
            </Button>
            <Button disabled>Unavailable</Button>
            <Button loading>Working</Button>
          </div>
          <p className="field-hint">
            Preview actions show a demo notification. No data is saved.
          </p>
        </Card>
        <Card className="design-section">
          <h2>A state for everything.</h2>
          <div className="component-row">
            <Badge>Draft</Badge>
            <Badge status="success">Approved</Badge>
            <Badge status="warning">Pending</Badge>
            <Badge status="danger">Rejected</Badge>
          </div>
          <Skeleton />
        </Card>
        <Card className="design-section">
          <h2>Keep it simple.</h2>
          <div className="component-stack">
            <div className="form-field">
              <label htmlFor="preview-email">Your email</label>
              <input
                id="preview-email"
                className="field-input"
                type="email"
                placeholder="you@example.com"
                aria-describedby="email-hint"
              />
              <p id="email-hint" className="field-hint">
                A component preview. Your address is not submitted.
              </p>
            </div>
            <div className="form-field">
              <label id="category-label">Event category</label>
              <Select.Root value={category} onValueChange={setCategory}>
                <Select.Trigger
                  className="select-trigger"
                  aria-labelledby="category-label"
                >
                  <Select.Value />
                  <Select.Icon>
                    <ChevronDown size={16} />
                  </Select.Icon>
                </Select.Trigger>
                <Select.Portal>
                  <Select.Content className="select-content" position="popper">
                    <Select.Viewport>
                      {[
                        ["music", "Live music"],
                        ["workshop", "Workshop"],
                        ["campus", "Campus event"],
                      ].map(([value, label]) => (
                        <Select.Item
                          className="select-item"
                          value={value}
                          key={value}
                        >
                          <Select.ItemText>{label}</Select.ItemText>
                        </Select.Item>
                      ))}
                    </Select.Viewport>
                  </Select.Content>
                </Select.Portal>
              </Select.Root>
            </div>
            <div className="checkbox-row">
              <Checkbox.Root
                id="preview-gift"
                className="checkbox-control"
                checked={accepted}
                onCheckedChange={(value) => setAccepted(value === true)}
              >
                <Checkbox.Indicator>
                  <Check size={15} />
                </Checkbox.Indicator>
              </Checkbox.Root>
              <label htmlFor="preview-gift">This ticket is a gift</label>
            </div>
          </div>
        </Card>
        <Card className="design-section">
          <h2>One for the memories.</h2>
          <div className="sample-ticket-row">
            <div>
              <Badge>Sample only</Badge>
              <h3>General admission</h3>
              <p>Illustrative ticket category</p>
              <span className="mono">BDT 1,200</span>
            </div>
            <Stepper value={quantity} onChange={setQuantity} />
          </div>
          <p className="field-hint" style={{ marginTop: 18 }}>
            Preview total: BDT {(quantity * 1200).toLocaleString("en-BD")}.
            Maximum 5 in this component demo.
          </p>
        </Card>
        <Card className="design-section">
          <h2>Room for a conversation.</h2>
          <Dialog.Root>
            <Dialog.Trigger asChild>
              <Button variant="secondary">Open preview dialog</Button>
            </Dialog.Trigger>
            <Dialog.Portal>
              <Dialog.Overlay className="dialog-overlay" />
              <Dialog.Content className="dialog-panel">
                <Dialog.Title className="dialog-title">
                  Make it a <em>moment.</em>
                </Dialog.Title>
                <Dialog.Description className="muted">
                  This is a design-system preview. Focus stays inside this
                  dialog; press Escape to close it.
                </Dialog.Description>
                <Dialog.Close
                  className="icon-button dialog-close"
                  aria-label="Close preview dialog"
                >
                  <X />
                </Dialog.Close>
                <Dialog.Close asChild>
                  <Button>Looks good</Button>
                </Dialog.Close>
              </Dialog.Content>
            </Dialog.Portal>
          </Dialog.Root>
        </Card>
        <Card className="design-section">
          <h2>A clear overview.</h2>
          <div className="design-table-wrap">
            <table className="design-table">
              <caption>Illustrative data for table styling only.</caption>
              <thead>
                <tr>
                  <th scope="col">Category</th>
                  <th scope="col">Price</th>
                  <th scope="col">Status</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>General</td>
                  <td>BDT 1,200</td>
                  <td>
                    <Badge>Draft</Badge>
                  </td>
                </tr>
                <tr>
                  <td>Student</td>
                  <td>BDT 600</td>
                  <td>
                    <Badge>Draft</Badge>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>
        <Card className="design-section">
          <div className="design-empty">
            <Ticket size={35} />
            <h2>A fresh start.</h2>
            <p>No tickets here yet. The next great moment is still ahead.</p>
          </div>
        </Card>
      </div>
      <Toast.Root className="toast-root" open={toast} onOpenChange={setToast}>
        <Toast.Title className="toast-title">
          That’s the TICKETÉ touch.
        </Toast.Title>
        <Toast.Description className="toast-description">
          This is a preview notification. No changes were saved.
        </Toast.Description>
        <Toast.Close className="toast-close">Dismiss</Toast.Close>
      </Toast.Root>
      <Toast.Viewport className="toast-viewport" />
    </Toast.Provider>
  );
}
