<mxfile host="app.diagrams.net" modified="2024-03-07T09:29:54.709Z" agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0" etag="IFFYxlVWO1z4EPXNvtmw" version="24.0.2" type="device">
  <diagram name="Page-1" id="6xTvG2J4V6oWj7Yo9foh">
    <mxGraphModel dx="2697" dy="1035" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="850" pageHeight="1100" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-4" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="253.5" y="550" width="746.5" height="190" as="geometry" />
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-33" value="" style="rounded=0;whiteSpace=wrap;html=1;fillColor=none;dashed=1;strokeWidth=3;" vertex="1" parent="1">
          <mxGeometry x="293.5" y="575" width="686.5" height="110" as="geometry" />
        </mxCell>
        <mxCell id="8z7EWTUwoPRm_el4eQDr-21" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=none;" parent="1" vertex="1">
          <mxGeometry x="210" y="60" width="730" height="160" as="geometry" />
        </mxCell>
        <mxCell id="8z7EWTUwoPRm_el4eQDr-4" value="Collection Metadata Store" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;" parent="1" vertex="1">
          <mxGeometry x="300" y="362" width="170" height="60" as="geometry" />
        </mxCell>
        <mxCell id="8z7EWTUwoPRm_el4eQDr-5" value="Vector DB" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" parent="1" vertex="1">
          <mxGeometry x="512.75" y="362" width="140" height="60" as="geometry" />
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-43" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;entryX=1;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="8z7EWTUwoPRm_el4eQDr-6" target="8z7EWTUwoPRm_el4eQDr-30">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="260" y="410" />
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="8z7EWTUwoPRm_el4eQDr-6" value="Data Source&lt;div&gt;Scanning/Crawling&lt;/div&gt;" style="rounded=0;whiteSpace=wrap;html=1;" parent="1" vertex="1">
          <mxGeometry x="240" y="120" width="120" height="60" as="geometry" />
        </mxCell>
        <mxCell id="8z7EWTUwoPRm_el4eQDr-7" value="Data Source&lt;div&gt;Filtering&lt;/div&gt;" style="rounded=0;whiteSpace=wrap;html=1;" parent="1" vertex="1">
          <mxGeometry x="395.5" y="120" width="134.5" height="60" as="geometry" />
        </mxCell>
        <mxCell id="8z7EWTUwoPRm_el4eQDr-8" value="Data Files&lt;div&gt;Parsing and Chunking&lt;/div&gt;" style="rounded=0;whiteSpace=wrap;html=1;" parent="1" vertex="1">
          <mxGeometry x="565.13" y="120" width="163.25" height="60" as="geometry" />
        </mxCell>
        <mxCell id="8z7EWTUwoPRm_el4eQDr-9" value="Chunks&amp;nbsp;&lt;div&gt;Embedding&lt;/div&gt;&lt;div&gt;and&lt;/div&gt;&lt;div&gt;Metadata&lt;/div&gt;" style="rounded=0;whiteSpace=wrap;html=1;" parent="1" vertex="1">
          <mxGeometry x="765" y="120" width="165" height="60" as="geometry" />
        </mxCell>
        <mxCell id="8z7EWTUwoPRm_el4eQDr-23" value="" style="endArrow=classic;html=1;rounded=0;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" parent="1" source="8z7EWTUwoPRm_el4eQDr-6" target="8z7EWTUwoPRm_el4eQDr-7" edge="1">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="490" y="310" as="sourcePoint" />
            <mxPoint x="540" y="260" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="8z7EWTUwoPRm_el4eQDr-24" value="" style="endArrow=classic;html=1;rounded=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;exitX=1;exitY=0.5;exitDx=0;exitDy=0;" parent="1" target="8z7EWTUwoPRm_el4eQDr-8" edge="1" source="8z7EWTUwoPRm_el4eQDr-7">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="500" y="190" as="sourcePoint" />
            <mxPoint x="390" y="200" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="8z7EWTUwoPRm_el4eQDr-25" value="" style="endArrow=classic;html=1;rounded=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;exitX=1;exitY=0.5;exitDx=0;exitDy=0;" parent="1" source="8z7EWTUwoPRm_el4eQDr-8" target="8z7EWTUwoPRm_el4eQDr-9" edge="1">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="510" y="200" as="sourcePoint" />
            <mxPoint x="530" y="200" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="8z7EWTUwoPRm_el4eQDr-27" value="" style="endArrow=classic;html=1;rounded=0;exitX=0.25;exitY=1;exitDx=0;exitDy=0;startArrow=classic;startFill=1;entryX=0.75;entryY=0;entryDx=0;entryDy=0;" parent="1" source="8z7EWTUwoPRm_el4eQDr-9" target="8z7EWTUwoPRm_el4eQDr-5" edge="1">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="480" y="310" as="sourcePoint" />
            <mxPoint x="580" y="80" as="targetPoint" />
            <Array as="points">
              <mxPoint x="806" y="300" />
              <mxPoint x="618" y="300" />
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="8z7EWTUwoPRm_el4eQDr-29" value="" style="endArrow=classic;startArrow=classic;html=1;rounded=0;entryX=0.25;entryY=0;entryDx=0;entryDy=0;exitX=0.5;exitY=1;exitDx=0;exitDy=0;" parent="1" source="8z7EWTUwoPRm_el4eQDr-7" target="8z7EWTUwoPRm_el4eQDr-5" edge="1">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="410" y="310" as="sourcePoint" />
            <mxPoint x="460" y="260" as="targetPoint" />
            <Array as="points">
              <mxPoint x="463" y="300" />
              <mxPoint x="550" y="300" />
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="8z7EWTUwoPRm_el4eQDr-41" value="&lt;font style=&quot;font-size: 18px;&quot;&gt;&lt;b&gt;Indexing Job&lt;/b&gt;&lt;/font&gt;" style="text;html=1;align=center;verticalAlign=middle;resizable=0;points=[];autosize=1;strokeColor=none;fillColor=none;fontSize=16;" parent="1" vertex="1">
          <mxGeometry x="510" y="215" width="130" height="40" as="geometry" />
        </mxCell>
        <mxCell id="8z7EWTUwoPRm_el4eQDr-80" value="Cron&lt;div&gt;Schedule&lt;/div&gt;&lt;div&gt;or Manual&lt;/div&gt;" style="rounded=0;whiteSpace=wrap;html=1;" parent="1" vertex="1">
          <mxGeometry x="30" y="110" width="120" height="60" as="geometry" />
        </mxCell>
        <mxCell id="8z7EWTUwoPRm_el4eQDr-81" value="" style="endArrow=classic;html=1;rounded=0;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" parent="1" source="8z7EWTUwoPRm_el4eQDr-80" target="8z7EWTUwoPRm_el4eQDr-21" edge="1">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="370" y="150" as="sourcePoint" />
            <mxPoint x="420" y="100" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="8z7EWTUwoPRm_el4eQDr-82" value="" style="endArrow=classic;startArrow=classic;html=1;rounded=0;exitX=0.196;exitY=0.992;exitDx=0;exitDy=0;exitPerimeter=0;" parent="1" source="8z7EWTUwoPRm_el4eQDr-21" edge="1">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="410" y="250" as="sourcePoint" />
            <mxPoint x="353" y="360" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-1" value="&lt;div&gt;GPT LLM&lt;/div&gt;(Azure OpenAI)&lt;div&gt;models&lt;/div&gt;" style="rounded=0;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="997.5" y="397" width="120" height="60" as="geometry" />
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-2" value="&lt;div&gt;&lt;/div&gt;&lt;div&gt;Language models&lt;/div&gt;&lt;div&gt;from other providers&lt;/div&gt;" style="rounded=0;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="997.5" y="467" width="120" height="60" as="geometry" />
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-9" value="Fetch&lt;div&gt;Collection&lt;/div&gt;&lt;div&gt;Metadata&lt;/div&gt;" style="rounded=0;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="324" y="598.75" width="151" height="60" as="geometry" />
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-38" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="ho5sq9B0i_K1lFmaLsdT-10" target="ho5sq9B0i_K1lFmaLsdT-11">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-10" value="Retrieval&amp;nbsp;&lt;div&gt;/ Multi-step Agents&lt;/div&gt;" style="rounded=0;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="505.5" y="598.75" width="154.5" height="60" as="geometry" />
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-39" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="ho5sq9B0i_K1lFmaLsdT-11" target="ho5sq9B0i_K1lFmaLsdT-12">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-11" value="Answer Generation" style="rounded=0;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="690" y="598.75" width="120" height="60" as="geometry" />
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-12" value="Metadata&lt;div&gt;Enrichment&lt;/div&gt;" style="rounded=0;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="840" y="598.75" width="120" height="60" as="geometry" />
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-13" value="" style="endArrow=classic;html=1;rounded=0;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="ho5sq9B0i_K1lFmaLsdT-9" target="ho5sq9B0i_K1lFmaLsdT-10">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="583.5" y="750" as="sourcePoint" />
            <mxPoint x="633.5" y="700" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-16" value="" style="endArrow=classic;html=1;rounded=0;startArrow=classic;startFill=1;" edge="1" parent="1" source="8z7EWTUwoPRm_el4eQDr-5" target="ho5sq9B0i_K1lFmaLsdT-10">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="570" y="390" as="sourcePoint" />
            <mxPoint x="570" y="670" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-20" value="TrueFoundry&lt;div&gt;LLM&amp;nbsp;&lt;/div&gt;&lt;div&gt;Gateway&lt;/div&gt;" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
          <mxGeometry x="772.5" y="362" width="150" height="60" as="geometry" />
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-21" value="Text Ada&lt;div&gt;Embedding Model&lt;/div&gt;" style="rounded=0;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="997.5" y="257" width="120" height="60" as="geometry" />
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-22" value="Embedding Models&lt;div&gt;from Other Providers&lt;/div&gt;" style="rounded=0;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="997.5" y="327" width="120" height="60" as="geometry" />
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-23" value="" style="endArrow=classic;html=1;rounded=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;exitX=1;exitY=0.5;exitDx=0;exitDy=0;" edge="1" parent="1" source="ho5sq9B0i_K1lFmaLsdT-20" target="ho5sq9B0i_K1lFmaLsdT-21">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="970" y="394.5" as="sourcePoint" />
            <mxPoint x="1577.5" y="427.5" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-24" value="" style="endArrow=classic;html=1;rounded=0;dashed=1;entryX=0;entryY=0.5;entryDx=0;entryDy=0;exitX=1;exitY=0.5;exitDx=0;exitDy=0;" edge="1" parent="1" source="ho5sq9B0i_K1lFmaLsdT-20" target="ho5sq9B0i_K1lFmaLsdT-22">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="920" y="380" as="sourcePoint" />
            <mxPoint x="997.5" y="374.5" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-26" value="" style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#232F3D;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.user;" vertex="1" parent="1">
          <mxGeometry x="100" y="604.75" width="78" height="78" as="geometry" />
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-27" value="" style="endArrow=classic;html=1;rounded=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" target="ho5sq9B0i_K1lFmaLsdT-1">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="920" y="390" as="sourcePoint" />
            <mxPoint x="997.5" y="444.5" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-28" value="" style="endArrow=classic;html=1;rounded=0;dashed=1;entryX=0;entryY=0.5;entryDx=0;entryDy=0;exitX=1;exitY=0.5;exitDx=0;exitDy=0;" edge="1" parent="1" target="ho5sq9B0i_K1lFmaLsdT-2" source="ho5sq9B0i_K1lFmaLsdT-20">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="970" y="394.5" as="sourcePoint" />
            <mxPoint x="1397.5" y="217.5" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-30" value="" style="endArrow=classic;startArrow=classic;html=1;rounded=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="ho5sq9B0i_K1lFmaLsdT-26" target="ho5sq9B0i_K1lFmaLsdT-4">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="208.9545454545455" y="630" as="sourcePoint" />
            <mxPoint x="623.5" y="580" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-31" value="" style="endArrow=classic;startArrow=classic;html=1;rounded=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;exitX=0.5;exitY=0;exitDx=0;exitDy=0;" edge="1" parent="1" source="ho5sq9B0i_K1lFmaLsdT-11" target="ho5sq9B0i_K1lFmaLsdT-20">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="913.5" y="680" as="sourcePoint" />
            <mxPoint x="983.5" y="680" as="targetPoint" />
            <Array as="points">
              <mxPoint x="750" y="392" />
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-32" value="&lt;font style=&quot;font-size: 18px;&quot;&gt;&lt;b&gt;Backend API Service&lt;/b&gt;&lt;/font&gt;" style="text;html=1;align=center;verticalAlign=middle;resizable=0;points=[];autosize=1;strokeColor=none;fillColor=none;fontSize=16;" vertex="1" parent="1">
          <mxGeometry x="565" y="735" width="200" height="40" as="geometry" />
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-35" value="" style="endArrow=classic;startArrow=classic;html=1;rounded=0;entryX=0.351;entryY=1.032;entryDx=0;entryDy=0;exitX=0.25;exitY=0;exitDx=0;exitDy=0;entryPerimeter=0;" edge="1" parent="1" source="ho5sq9B0i_K1lFmaLsdT-9" target="8z7EWTUwoPRm_el4eQDr-4">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="470" y="470" as="sourcePoint" />
            <mxPoint x="520" y="420" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-37" value="&lt;b&gt;&lt;font style=&quot;font-size: 18px;&quot;&gt;Application Query Controller&lt;/font&gt;&lt;/b&gt;" style="text;html=1;align=center;verticalAlign=middle;resizable=0;points=[];autosize=1;strokeColor=none;fillColor=none;fontSize=16;" vertex="1" parent="1">
          <mxGeometry x="511.75" y="680" width="270" height="40" as="geometry" />
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-46" value="" style="group" vertex="1" connectable="0" parent="1">
          <mxGeometry x="-120" y="270" width="200" height="280" as="geometry" />
        </mxCell>
        <mxCell id="8z7EWTUwoPRm_el4eQDr-30" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=none;" parent="ho5sq9B0i_K1lFmaLsdT-46" vertex="1">
          <mxGeometry width="200" height="280" as="geometry" />
        </mxCell>
        <mxCell id="8z7EWTUwoPRm_el4eQDr-1" value="" style="outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.aws3.bucket;fillColor=#E05243;gradientColor=none;" parent="ho5sq9B0i_K1lFmaLsdT-46" vertex="1">
          <mxGeometry x="111" y="24.5" width="60" height="61.5" as="geometry" />
        </mxCell>
        <mxCell id="8z7EWTUwoPRm_el4eQDr-2" value="" style="sketch=0;pointerEvents=1;shadow=0;dashed=0;html=1;strokeColor=none;fillColor=#505050;labelPosition=center;verticalLabelPosition=bottom;verticalAlign=top;outlineConnect=0;align=center;shape=mxgraph.office.devices.hard_disk;" parent="ho5sq9B0i_K1lFmaLsdT-46" vertex="1">
          <mxGeometry x="30" y="164.5" width="40" height="54" as="geometry" />
        </mxCell>
        <mxCell id="8z7EWTUwoPRm_el4eQDr-3" value="" style="sketch=0;shadow=0;dashed=0;html=1;strokeColor=none;labelPosition=center;verticalLabelPosition=bottom;verticalAlign=top;outlineConnect=0;align=center;shape=mxgraph.office.databases.database_cube;fillColor=#2072B8;" parent="ho5sq9B0i_K1lFmaLsdT-46" vertex="1">
          <mxGeometry x="26.5" y="30" width="47" height="52" as="geometry" />
        </mxCell>
        <mxCell id="8z7EWTUwoPRm_el4eQDr-31" value="TrueFoundry&lt;div&gt;Artifacts&lt;/div&gt;" style="text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;" parent="ho5sq9B0i_K1lFmaLsdT-46" vertex="1">
          <mxGeometry x="20" y="90" width="60" height="30" as="geometry" />
        </mxCell>
        <mxCell id="8z7EWTUwoPRm_el4eQDr-32" value="Local Disk" style="text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;" parent="ho5sq9B0i_K1lFmaLsdT-46" vertex="1">
          <mxGeometry x="20" y="224.5" width="60" height="30" as="geometry" />
        </mxCell>
        <mxCell id="8z7EWTUwoPRm_el4eQDr-33" value="S3 Bucket" style="text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;" parent="ho5sq9B0i_K1lFmaLsdT-46" vertex="1">
          <mxGeometry x="111" y="94.5" width="60" height="30" as="geometry" />
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-44" value="" style="shape=datastore;whiteSpace=wrap;html=1;" vertex="1" parent="ho5sq9B0i_K1lFmaLsdT-46">
          <mxGeometry x="111" y="158.5" width="60" height="60" as="geometry" />
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-45" value="DB Sources" style="text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;" vertex="1" parent="ho5sq9B0i_K1lFmaLsdT-46">
          <mxGeometry x="111" y="224.5" width="60" height="30" as="geometry" />
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-47" value="" style="endArrow=none;dashed=1;html=1;dashPattern=1 3;strokeWidth=2;rounded=0;entryX=0.5;entryY=1;entryDx=0;entryDy=0;exitX=0.5;exitY=1;exitDx=0;exitDy=0;" edge="1" parent="1" source="ho5sq9B0i_K1lFmaLsdT-12" target="8z7EWTUwoPRm_el4eQDr-30">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="960" y="820" as="sourcePoint" />
            <mxPoint x="-30" y="570" as="targetPoint" />
            <Array as="points">
              <mxPoint x="900" y="820" />
              <mxPoint x="-20" y="820" />
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-48" value="User" style="text;html=1;align=center;verticalAlign=middle;resizable=0;points=[];autosize=1;strokeColor=none;fillColor=none;" vertex="1" parent="1">
          <mxGeometry x="110" y="700" width="50" height="30" as="geometry" />
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-50" value="" style="endArrow=classic;startArrow=classic;html=1;rounded=0;exitX=0.5;exitY=1;exitDx=0;exitDy=0;" edge="1" parent="1" source="8z7EWTUwoPRm_el4eQDr-9" target="ho5sq9B0i_K1lFmaLsdT-20">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="363" y="229" as="sourcePoint" />
            <mxPoint x="363" y="370" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-52" value="&lt;font style=&quot;font-size: 18px;&quot;&gt;&lt;b&gt;Data Sources&lt;/b&gt;&lt;/font&gt;" style="text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;" vertex="1" parent="1">
          <mxGeometry x="-90" y="240" width="140" height="30" as="geometry" />
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-53" value="&lt;font style=&quot;font-size: 18px;&quot;&gt;&lt;b&gt;Data Loader&lt;/b&gt;&lt;/font&gt;" style="text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;" vertex="1" parent="1">
          <mxGeometry x="330" y="80" width="120" height="30" as="geometry" />
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-54" value="&lt;font style=&quot;font-size: 18px;&quot;&gt;&lt;b&gt;Parser&lt;/b&gt;&lt;/font&gt;" style="text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;" vertex="1" parent="1">
          <mxGeometry x="576.75" y="80" width="120" height="30" as="geometry" />
        </mxCell>
        <mxCell id="ho5sq9B0i_K1lFmaLsdT-55" value="&lt;font style=&quot;font-size: 18px;&quot;&gt;&lt;b&gt;Embedder&lt;/b&gt;&lt;/font&gt;" style="text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;" vertex="1" parent="1">
          <mxGeometry x="787.5" y="80" width="120" height="30" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
