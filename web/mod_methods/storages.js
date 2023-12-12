import { DEBUG_STRING, getNodeByLink, enableOnlyRelatedNodes, findWidgetByName, executeAndWaitForLoopchain } from "../utils.js"
import * as shared from '../comfy_shared.js'


export const ImageStorageExportLoop = {
    beforeDef(nodeType, nodeData, app) {
        nodeType.prototype.onNodeCreated = function () {
            this.changeMode(LiteGraph.ALWAYS);
            const loopPreview = this.addCustomWidget(
                DEBUG_STRING('loop_preview', 'Iteration: Idle')
            );
            loopPreview.parent = this;

            this.onRemoved = () => {
                for (const w of this.widgets) {
                    if (w.canvas) {
                        w.canvas.remove()
                    }
                    w.onRemoved?.()
                }
                app.canvas.setDirty(true)
            }
        }
    },
    whenCreated(node, app) {
        const getLoopNum = async (key, batchSize) => {
            const { result: numLoop } = await fetch(`/loopchain/dataloader_length?type=image&key=${key.value}&batch_size=${batchSize.value}`)
              .then(re => re.json())
            return numLoop;
        }

        const queueBtn = node.addWidget('button', `Queue`, 'queue', function () {
            const loopIndex = findWidgetByName(node, 'loop_idx');
            loopIndex.value = 0;
            return (async _ => {
                const key = findWidgetByName(node, "key");
                const batchSize = findWidgetByName(node, "batch_size");
                const loopPreview = findWidgetByName(node, 'loop_preview');
                const loopEnd = findWidgetByName(node, "loop_end");
                loopPreview.value = 'Iteration: Idle';
                app.canvas.setDirty(true);

                let numLoop = await getLoopNum(key, batchSize);
                if (numLoop === -1) {
                    loopPreview.value = `"${key.value}" not found. 🤔`
                    return;
                }

                // If no loop end is provided, we assume we want to run as many loops as the first
                // queue execution finds.
                if (loopEnd.value === 0) {
                    loopEnd.value = numLoop;
                }

                for (let i = 0; i < numLoop && i < loopEnd.value; i++) {
                    await executeAndWaitForLoopchain(app, node);

                    // Check for new data added to key
                    numLoop = await getLoopNum(key, batchSize);

                    loopPreview.value = `current loop: ${i + 1}/${numLoop}`;
                    app.canvas.setDirty(true);
                    loopIndex.value++;
                }
                loopPreview.value = 'Done 😎!';
                app.canvas.setDirty(true);
            })();

        });
        let isShowed = true;
        setInterval(_ => {
            if (node.inputs[0].link && isShowed) {
                shared.hideWidgetForGood(node, queueBtn);
                isShowed = false;
            }
            if (!node.inputs[0].link && !isShowed) {
                shared.showWidget(queueBtn);
                isShowed = true;
            }
        }, 0)
    }
}
export const ImageStorageExport = {
    whenCreated(node, app) {
        node.addWidget('button', `Queue`, 'queue', function () {
            return (async () => await executeAndWaitForLoopchain(app, node))();
        });
    }
}
export const ImageStorageReset = {
    whenCreated(node, app) {
        node.addWidget('button', `Queue`, 'queue', function () {
            return (async () => await executeAndWaitForLoopchain(app, node))();
        });
    }
}
export const LatentStorageReset = {
    whenCreated(node, app) {
        node.addWidget('button', `Queue`, 'queue', function () {
            return (async () => await executeAndWaitForLoopchain(app, node))();
        });
    }
}
export const ImageToImageStorage = {
    whenCreated(node, app) {
        node.addWidget('button', `Queue`, 'queue', function () {
            return (async () => await executeAndWaitForLoopchain(app, node))();
        });
    }
}
export const FolderToImageStorage = {
    whenCreated(node, app) {
        node.addWidget('button', `Queue`, 'queue', function () {
            return (async () => await executeAndWaitForLoopchain(app, node))();
        });
    }
}
